import json
import os
import time
from openai import OpenAI
from testflow.common import ROOT, RAW, load_environment
from testflow.layout import prepare


def get_client():
    """Read credentials at call time, never from source-code literals."""
    load_environment()
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("Configure DEEPSEEK_API_KEY in the environment or project .env")
    return OpenAI(api_key=key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                  timeout=90, max_retries=1)


def generate_playwright_script(test_case: dict) -> str:
    """
    Generate a Playwright + pytest test script from a UI test case.
    """
    prompt = f"""
    You are a test automation engineer. Write a Python pytest test script using the Playwright library for the following test case.

    Requirements:
    - Use `from playwright.sync_api import Page, expect`
    - Use `page.goto()` to navigate to URLs
    - Use `page.locator()` to find elements and perform actions (.click(), .fill(), etc.)
    - Use `expect(page.locator(...)).to_be_visible()` or `to_contain_text()` for assertions
    - Playwright's auto-waiting is enabled by default. Do NOT use `time.sleep()`.
    - Use `@pytest.fixture` for browser setup and teardown (or use `browser.new_page()` inside test)
    - The test function should be named `test_xxx()`.
    - Include clear print statements for test progress.

    Test Case:
    - Test ID: {test_case.get('test_id')}
    - Test Name: {test_case.get('test_name')}
    - Preconditions: {test_case.get('preconditions')}
    - Steps: {test_case.get('test_steps')}
    - Expected Result: {test_case.get('expected_result')}

    Output ONLY the raw Python code. Do NOT include markdown formatting, explanations, or code blocks.
    """

    try:
        response = get_client().chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a Python test automation engineer. Output raw Python code only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] Failed to generate Playwright script: {e}")
        return ""


def generate_api_script(test_case: dict) -> str:
    """
    Generate a pytest + requests API test script from an API test case.
    """
    prompt = f"""
    You are a test automation engineer. Write a Python pytest + requests API test script for the following test case.

    Requirements:
    - Use `import requests`
    - Use `import pytest`
    - Define a test function with `def test_xxx():`
    - Every HTTP request MUST start with `response = requests.xxx(...)`. NEVER write `= requests.xxx(...)` without `response` before the `=`.
    - The response object MUST be named exactly `response` (not `_code`, not `resp`). All assertions MUST use `response.status_code` and `response.json()`.
    - You MUST actually call a real `requests.*` method (GET/POST/PUT/DELETE). DO NOT hardcode status codes without sending a real request.
    - Use `assert` statements to verify response status codes and JSON fields.
    - Include `BASE_URL = "https://automationexercise.com"` configuration.
    - For POST/PUT/DELETE requests, include proper form data or JSON payload.

    Test Case:
    - Test ID: {test_case.get('test_id')}
    - Test Name: {test_case.get('test_name')}
    - Preconditions: {test_case.get('preconditions')}
    - Steps: {test_case.get('test_steps')}
    - Expected Result: {test_case.get('expected_result')}

    Output ONLY the raw Python code. Do NOT include markdown formatting, explanations, or code blocks.
    """

    try:
        response = get_client().chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a Python API test automation engineer. Output raw Python code only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] Failed to generate API script: {e}")
        return ""


def clean_code(code: str) -> str:
    """
    Remove markdown code fences if AI accidentally includes them.
    """
    code = code.strip()
    if code.startswith("```python"):
        code = code[9:].strip()
    if code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()
    return code


def main():
    prepare(ROOT)
    print("[INFO] Loading generated test cases...")

    try:
        with open(ROOT / "generated_test_cases.json", "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print("[ERROR] generated_test_cases.json not found. Please run test_case_gen.py first.")
        return

    print(f"[INFO] Loaded {len(test_cases)} test cases.")

    # Create output directory
    RAW.mkdir(parents=True, exist_ok=True)

    print("[INFO] Generating test scripts...")

    for idx, case in enumerate(test_cases, 1):
        test_id = case.get("test_id", f"TC_{idx:03d}")
        test_type = case.get("test_type", "UI")

        print(f"[INFO] Processing {test_id} ({test_type})...")
        if not test_id.startswith('TC_') or not test_id[3:].isdigit():
            raise ValueError('Invalid test ID')
        filename = RAW / f"test_{test_id.lower()}.py"
        if filename.exists():
            print(f"[INFO] Preserving existing {filename}; use the repair workflow for changes.")
            continue

        try:
            if test_type.upper() == "UI":
                script_code = generate_playwright_script(case)
            elif test_type.upper() == "API":
                script_code = generate_api_script(case)
            else:
                print(f"[WARNING] Unknown test_type '{test_type}' for {test_id}, skipping.")
                continue

            if not script_code:
                print(f"[WARNING] No code generated for {test_id}, skipping.")
                continue

            script_code = clean_code(script_code)

            with open(filename, "x", encoding="utf-8") as f:
                f.write(script_code)

            print(f"[SUCCESS] Saved to {filename}")

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"[ERROR] Failed to generate script for {test_id}: {e}")

    print("[INFO] New scripts saved to generated_tests/case_raw; existing scripts preserved.")


if __name__ == "__main__":
    main()
