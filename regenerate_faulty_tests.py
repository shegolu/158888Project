# regenerate_faulty_tests.py
import json
import os
import time

# Import the existing generation functions from your original script
from script_gen import generate_api_script, generate_playwright_script, clean_code

# Define the target IDs that need fixing
TARGET_IDS = ["TC_032", "TC_039", "TC_040", "TC_041", "TC_042"]


def main():
    print("[INFO] Loading generated test cases from JSON...")

    try:
        with open("generated_test_cases.json", "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print("[ERROR] generated_test_cases.json not found.")
        return

    print(f"[INFO] Loaded {len(test_cases)} test cases.")
    print(f"[INFO] Targeting faulty test cases: {TARGET_IDS}")

    # Ensure output directory exists
    os.makedirs("generated_tests", exist_ok=True)

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

            filename = f"generated_tests/test_{test_id.lower()}.py"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(clean_script)

            print(f"[SUCCESS] Overwrote {filename}")

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"[ERROR] Failed for {test_id}: {e}")

    print("[INFO] Regeneration complete for faulty test cases.")


if __name__ == "__main__":
    main()