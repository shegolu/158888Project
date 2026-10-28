"""Aggressive AI repair for fail/timeout cases selected from the final table."""

import argparse
import csv
import io
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from testflow.ai import DeepSeek
from testflow.common import ROOT, RAW, load_environment, redact, write_json
from testflow.runner import execute


FAIL_IDS = {
    "TC_001", "TC_005", "TC_008", "TC_012", "TC_014", "TC_018", "TC_032",
}
TIMEOUT_IDS = {
    "TC_003", "TC_004", "TC_006", "TC_009", "TC_010", "TC_011", "TC_013",
    "TC_015", "TC_016", "TC_017", "TC_019", "TC_021", "TC_022", "TC_023",
    "TC_024", "TC_025", "TC_026", "TC_027",
}


SYSTEM = r"""
You repair generated pytest / Playwright / requests tests.

You will be told the repair mode:
- fail: fix business logic, locators, waits, selectors, or test-flow defects.
- timeout: first make navigation robust so it does not hang on this flaky public
  site, then fix any business logic, locator, wait, or assertion defect.

Return ONE JSON object with these fields:
{
  "summary": "short factual explanation of what was changed and why",
  "changes": ["one clear change item per string"],
  "repaired_code": "full Python source, raw code only"
}

Rules:
1. Preserve the original test intent, test function names, expected business
   results, assertion expectations, HTTP status/business codes, and input data.
2. Never use pytest.skip/xfail, never catch an assertion/error just to pass,
   never hardcode success, never remove an assertion, and never insert an early
   return that bypasses the test.
3. For timeout mode, before any page.goto add a page.route helper that:
   - aborts known ad/tracker hosts,
   - fulfills automationexercise.com/static/js/* requests with an empty
     JavaScript body.
   Then use a small retry loop around page.goto with wait_until="commit" and a
   short timeout, followed by waiting for a business-critical visible element
   before yielding the fixture/page.
4. For fail mode, do not weaken assertions; fix only the code needed to satisfy
   the original expectation.
5. Use locator strategies such as .first/.last/.nth, has_text=..., header
   scoping, or waiting for modal/button visibility when strict-mode or
   synchronization problems are present.
6. `repaired_code` must be complete Python and must compile. Do not wrap it in
   markdown fences or commentary.
"""


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def clean_json_text(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def load_case_data():
    return {c["test_id"]: c for c in json.loads((ROOT / "generated_test_cases.json").read_text(encoding="utf-8"))}


def load_existing_result(test_id, base_dir):
    path = base_dir / "initial" / f"test_{test_id.lower()}" / "result.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_retest_result(test_id):
    candidates = sorted(
        ROOT.glob(f"runs/aggressive_ai_repair_*/cases/{test_id}/round1/retest/result.json"),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        raise ValueError(f"no retest result for {test_id}")
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


def dom_excerpt(result):
    dom = []
    for item in result.get("evidence", {}).get("artifacts", []):
        path = Path(item)
        if path.suffix == ".html" and path.is_file():
            dom.append({"path": str(path), "excerpt": path.read_text(encoding="utf-8", errors="replace")[:24000]})
    return dom


def build_user_payload(result, case, mode):
    source = Path(result["source_snapshot"]).read_text(encoding="utf-8")
    log = Path(result["process_log"]).read_text(encoding="utf-8", errors="replace")[-18000:]
    return {
        "mode": mode,
        "test_case": case,
        "source": source,
        "execution": {
            k: result.get(k)
            for k in ("status", "phase", "classification", "duration", "exit_code", "error", "timed_out")
        },
        "log_tail": log,
        "dom": dom_excerpt(result),
    }


def validate_repaired(original, code, test_id):
    if not isinstance(code, str) or not code.strip():
        raise ValueError("repaired_code is empty")
    compile(code, f"<repair-{test_id}>", "exec")
    original_funcs = set(re.findall(r"def (test_\w+)\s*\(", original))
    repaired_funcs = set(re.findall(r"def (test_\w+)\s*\(", code))
    if original_funcs - repaired_funcs:
        raise ValueError(f"missing test functions: {sorted(original_funcs - repaired_funcs)}")


def call_ai(client, mode, result, case, directory):
    payload = build_user_payload(result, case, mode)
    request = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": redact(json.dumps(payload, ensure_ascii=False))},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }
    write_json(directory / "ai_request.json", request)
    response = client.chat.completions.create(**request)
    write_json(directory / "ai_response.json", response.model_dump())
    content = clean_json_text(response.choices[0].message.content)
    decoder = json.JSONDecoder()
    value, _ = decoder.raw_decode(content.lstrip())
    if not isinstance(value.get("summary"), str):
        raise ValueError("AI summary missing")
    if not isinstance(value.get("changes"), list) or not all(isinstance(x, str) for x in value["changes"]):
        raise ValueError("AI changes missing")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="+", help="Target test IDs. Defaults to all fail+timeout IDs.")
    parser.add_argument("--rounds", type=int, choices=[1, 2], default=1)
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--block-ads", action="store_true")
    parser.add_argument("--existing-run", default=str(ROOT / "runs" / "failed_ai_repair_20261017T090203Z-de2638d9"))
    parser.add_argument("--use-retest", action="store_true", help="Use the latest aggressive-run retest result as AI evidence.")
    args = parser.parse_args()

    load_environment()
    os.environ["TESTFLOW_BLOCK_ADS"] = "1" if args.block_ads else "0"
    os.environ["TESTFLOW_NAVIGATION_TIMEOUT_MS"] = "0"
    os.environ["TESTFLOW_REQUEST_TIMEOUT_SECONDS"] = "0"

    cases = load_case_data()
    target = args.ids or sorted(FAIL_IDS | TIMEOUT_IDS)
    target = sorted(set(target))
    unknown = [i for i in target if i not in cases]
    if unknown:
        raise ValueError(f"Unknown case IDs: {unknown}")

    analyzer = DeepSeek(system_prompt=SYSTEM)
    client = analyzer.client
    run_id = now_utc() + "-" + uuid.uuid4().hex[:8]
    run_dir = ROOT / "runs" / f"aggressive_ai_repair_{run_id}"
    run_dir.mkdir(parents=True)
    write_json(run_dir / "configuration.json", {
        "created_at_utc": run_id,
        "target_ids": target,
        "max_rounds": args.rounds,
        "per_case_timeout": args.timeout,
        "block_ads": args.block_ads,
        "existing_evidence_run": args.existing_run,
    })

    rows = []
    for index, test_id in enumerate(target, 1):
        mode = "timeout" if test_id in TIMEOUT_IDS else "fail"
        raw_path = RAW / f"test_{test_id.lower()}.py"
        case_dir = run_dir / "cases" / test_id
        case_dir.mkdir(parents=True, exist_ok=True)
        before = raw_path.read_text(encoding="utf-8")
        (case_dir / "before.py").write_text(before, encoding="utf-8")

        try:
            result = load_retest_result(test_id) if args.use_retest else load_existing_result(test_id, Path(args.existing_run))
            if result.get("source_sha256"):
                current_sha = __import__("hashlib").sha256(raw_path.read_bytes()).hexdigest()
                if result["source_sha256"] != current_sha:
                    raise ValueError("current raw does not match the saved initial evidence; refusing stale repair")
        except Exception as exc:
            rows.append({"test_id": test_id, "mode": mode, "status": "skipped", "error": redact(exc)})
            continue

        print(f"[{index}/{len(target)}] {test_id} ({mode}) AI repair", flush=True)
        analysis_dir = case_dir / "round1"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        try:
            analysis = call_ai(client, mode, result, cases[test_id], analysis_dir)
            repaired_code = analysis["repaired_code"]
            validate_repaired(before, repaired_code, test_id)
            (analysis_dir / "candidate.py").write_text(repaired_code, encoding="utf-8")
            raw_path.write_text(repaired_code, encoding="utf-8")
            retest = execute(raw_path, analysis_dir / "retest", ROOT, timeout=args.timeout)
            status = "modified"
        except Exception as exc:
            analysis = {"summary": "repair failed", "changes": [], "repaired_code": None}
            repaired_code = None
            retest = None
            status = "error"
            error = redact(exc)

        row = {
            "test_id": test_id,
            "mode": mode,
            "status": status,
            "initial_status": result.get("status"),
            "initial_classification": result.get("classification"),
            "ai_summary": analysis.get("summary", ""),
            "ai_changes": " || ".join(analysis.get("changes", [])),
            "retest_status": retest.get("status") if retest else "",
            "retest_classification": retest.get("classification") if retest else "",
            "retest_error": (retest.get("error") or "")[-2000:] if retest else "",
            "before_path": str(case_dir / "before.py"),
            "candidate_path": str(analysis_dir / "candidate.py") if repaired_code else "",
            "error": error if status == "error" else "",
        }
        rows.append(row)
        write_json(analysis_dir / "repair_record.json", row)
        write_json(run_dir / "repair_records.json", rows)

    with (run_dir / "repair_records.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Report: {run_dir / 'repair_records.csv'}", flush=True)


if __name__ == "__main__":
    main()
