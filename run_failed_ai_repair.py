"""Run AI repair for failed cases only, one case at a time.

This script reads the combined_42_cases.csv as the source of truth, skips cases
already marked `passed`, and processes only `failed` cases. It does not trigger
the full 42-case regression used by the main pipeline, so already-passing cases
are neither run nor modified.
"""

import argparse
import csv
import io
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from testflow.ai import DeepSeek
from testflow.common import ROOT, RAW, load_environment, redact, write_json
from testflow.pipeline import apply_repair
from testflow.runner import execute


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_failed_ids(csv_path):
    rows = list(csv.DictReader(io.StringIO(Path(csv_path).read_text(encoding="utf-8-sig"))))
    return [r["test_id"] for r in rows if r.get("status") != "passed"]


def load_cases():
    data = json.loads((ROOT / "generated_test_cases.json").read_text(encoding="utf-8"))
    return {item["test_id"]: item for item in data}


def short_error(result):
    text = result.get("error") or ""
    return text[-4000:]


def decision_reason(result, analysis):
    if result.get("classification") == "environment":
        return "Environment failures are not automatically repaired"
    if analysis.get("category") not in {"locator", "precondition", "collection"}:
        return "AI category is not in the allowed auto-repair set"
    if not analysis.get("safe_to_repair"):
        return "AI returned safe_to_repair=false"
    if analysis.get("confidence", 0) < 0.85:
        return "AI confidence is below the 0.85 auto-repair threshold"
    if not analysis.get("evidence"):
        return "AI did not provide evidence"
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(ROOT / "runs" / "combined_42_cases.csv"))
    parser.add_argument("--ids", nargs="+", help="Optional override; default reads failed IDs from --csv")
    parser.add_argument("--rounds", type=int, choices=[1, 2], default=1)
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--block-ads", action="store_true")
    args = parser.parse_args()

    load_environment()
    os.environ["TESTFLOW_BLOCK_ADS"] = "1" if args.block_ads else "0"
    os.environ["TESTFLOW_NAVIGATION_TIMEOUT_MS"] = "0"
    os.environ["TESTFLOW_REQUEST_TIMEOUT_SECONDS"] = "0"

    cases = load_cases()
    ids = args.ids or read_failed_ids(args.csv)
    ids = sorted(set(ids))
    unknown = [i for i in ids if i not in cases]
    if unknown:
        raise ValueError(f"Unknown case IDs: {unknown}")

    analyzer = DeepSeek(system_prompt=None)
    run_id = now_utc() + "-" + uuid.uuid4().hex[:8]
    run_dir = ROOT / "runs" / f"failed_ai_repair_{run_id}"
    run_dir.mkdir(parents=True)
    write_json(run_dir / "configuration.json", {
        "created_at_utc": run_id,
        "csv": str(args.csv),
        "selected_ids": ids,
        "max_rounds": args.rounds,
        "per_case_timeout": args.timeout,
        "block_ads": args.block_ads,
    })

    rows = []
    for index, test_id in enumerate(ids, 1):
        raw_path = RAW / f"test_{test_id.lower()}.py"
        if not raw_path.is_file():
            rows.append({"test_id": test_id, "initial_status": "missing", "error": "raw file missing"})
            continue

        initial_dir = run_dir / "initial" / f"test_{test_id.lower()}"
        print(f"[{index}/{len(ids)}] {test_id} initial", flush=True)
        initial = execute(raw_path, initial_dir, ROOT, timeout=args.timeout)
        current = initial
        attempts = []
        applied = 0
        final = initial

        if current["status"] == "failed":
            for round_no in range(1, args.rounds + 1):
                analysis_dir = run_dir / "repairs" / test_id / str(round_no)
                analysis_dir.mkdir(parents=True, exist_ok=True)
                (analysis_dir / "before.py").write_bytes(raw_path.read_bytes())
                context = dict(current)
                context["_analysis_directory"] = str(analysis_dir)
                try:
                    analysis = analyzer.analyze(context, cases[test_id])
                except Exception as exc:
                    analysis = {
                        "category": "unknown",
                        "summary": "AI analysis unavailable or invalid",
                        "evidence": [],
                        "suggestion": redact(exc),
                        "confidence": 0,
                        "safe_to_repair": False,
                        "repaired_code": None,
                        "provider": "unavailable",
                    }
                write_json(analysis_dir / "analysis.json", analysis)

                attempt = {
                    "round": round_no,
                    "analysis": analysis,
                    "decision": "human_review",
                    "reason": decision_reason(current, analysis),
                    "patch": None,
                    "retest": None,
                }
                if attempt["reason"] is None:
                    try:
                        attempt["patch"] = apply_repair(ROOT, current, analysis, analysis_dir)
                        attempt["decision"] = "applied"
                        applied += 1
                        retest = execute(raw_path, analysis_dir / "retest", ROOT, timeout=args.timeout)
                        attempt["retest"] = retest
                        current = retest
                    except Exception as exc:
                        attempt["decision"] = "human_review"
                        attempt["reason"] = redact(exc)
                attempts.append(attempt)
                write_json(analysis_dir / "decision.json", attempt)
                if current["status"] == "passed":
                    break

        final = current
        modified = applied > 0
        rows.append({
            "test_id": test_id,
            "test_type": cases[test_id]["test_type"],
            "initial_status": initial["status"],
            "initial_classification": initial.get("classification", ""),
            "initial_error": short_error(initial),
            "ai_rounds": len(attempts),
            "ai_last_category": attempts[-1]["analysis"]["category"] if attempts else "",
            "ai_last_confidence": attempts[-1]["analysis"]["confidence"] if attempts else "",
            "ai_last_summary": attempts[-1]["analysis"]["summary"] if attempts else "",
            "ai_last_suggestion": attempts[-1]["analysis"]["suggestion"] if attempts else "",
            "decision": attempts[-1]["decision"] if attempts else "not_analyzed",
            "decision_reason": attempts[-1]["reason"] if attempts else "",
            "applied_rounds": applied,
            "retest_status": attempts[-1]["retest"]["status"] if attempts and attempts[-1]["retest"] else "not_run",
            "final_status": final["status"],
            "final_classification": final.get("classification", ""),
            "final_error": short_error(final),
            "modified": modified,
            "modified_file": str(raw_path) if modified else "",
            "evidence_directory": final.get("directory", ""),
        })

        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        (run_dir / "case_analysis.csv").write_text(output.getvalue(), encoding="utf-8-sig", newline="")
        write_json(run_dir / "case_analysis.json", rows)

    print(f"Report: {run_dir / 'case_analysis.csv'}", flush=True)


if __name__ == "__main__":
    main()
