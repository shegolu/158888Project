# regenerate_faulty_tests.py
import json
import os
import time
from datetime import datetime, timezone
import uuid
from testflow.common import ROOT
from testflow.layout import prepare

# Import the existing generation functions from your original script
from script_gen import generate_api_script, generate_playwright_script, clean_code

# Define the target IDs that need fixing
TARGET_IDS = ["TC_032", "TC_039", "TC_040", "TC_041", "TC_042"]


def main():
    prepare(ROOT)
    print("[INFO] Loading generated test cases from JSON...")

    try:
        with open(ROOT / "generated_test_cases.json", "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print("[ERROR] generated_test_cases.json not found.")
        return

    print(f"[INFO] Loaded {len(test_cases)} test cases.")
    print(f"[INFO] Targeting faulty test cases: {TARGET_IDS}")

    # Ensure output directory exists
    output = ROOT / 'runs' / ('regeneration-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    output.mkdir(parents=True)

    for case in test_cases:
        test_id = case.get("test_id")
        
        # Skip if not in our fix list
        if test_id not in TARGET_IDS:
            continue

        test_type = case.get("test_type", "UI")
        print(f"[INFO] Regenerating {test_id} ({test_type})...")

        try:
            # Reuse the exact same generation logic
            if test_type.upper() == "UI":
                script_code = generate_playwright_script(case)
            elif test_type.upper() == "API":
                script_code = generate_api_script(case)
            else:
                print(f"[WARNING] Unknown type for {test_id}, skipping.")
                continue

            if not script_code:
                print(f"[WARNING] Empty code for {test_id}, skipping.")
                continue

            clean_script = clean_code(script_code)

            if not test_id.startswith('TC_') or not test_id[3:].isdigit():
                raise ValueError('Invalid test ID')
            filename = output / f"test_{test_id.lower()}.py"
            with open(filename, "x", encoding="utf-8") as f:
                f.write(clean_script)

            print(f"[SUCCESS] Proposal saved to {filename}; no working script overwritten")

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"[ERROR] Failed for {test_id}: {e}")

    print("[INFO] Regeneration complete for faulty test cases.")


if __name__ == "__main__":
    main()
