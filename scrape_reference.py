import requests
import re
import json


def scrape_automationexercise_test_cases():
    """
    Scrape official test case titles using regex on the entire page text.
    This is more robust than searching specific tags.
    """
    url = "https://automationexercise.com/test_cases"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to fetch page: {e}")
        return []

    # Use regex to find all patterns like "Test Case 1: Register User"
    # The pattern matches "Test Case" + number + ":" + any text until newline or HTML tag.
    raw_text = response.text
    matches = re.findall(r'Test Case \d+:\s*[^<>\n]+', raw_text)

    if not matches:
        print("[WARNING] No test cases found via regex. Printing page snippet for debug:")
        print(raw_text[:1000])
        return []

    # Deduplicate and clean up
    seen = set()
    unique_titles = []
    for title in matches:
        title_clean = title.strip()
        if title_clean not in seen:
            seen.add(title_clean)
            unique_titles.append(title_clean)

    # Build JSON structure
    reference_cases = []
    for idx, raw_title in enumerate(unique_titles, 1):
        # Extract the core name after the colon
        match = re.search(r'Test Case \d+:\s*(.+)', raw_title)
        if match:
            case_name = match.group(1).strip()
        else:
            case_name = raw_title

        reference_cases.append({
            "test_id": f"REF_{idx:03d}",
            "test_name": case_name,
            "test_type": "Unknown",
            "test_steps": [],
            "raw_title": raw_title
        })

    return reference_cases


if __name__ == "__main__":
    print("[INFO] Starting scrape with regex method...")
    cases = scrape_automationexercise_test_cases()

    if cases and len(cases) > 1:
        with open("reference_test_cases.json", "w", encoding="utf-8") as f:
            json.dump(cases, f, indent=2, ensure_ascii=False)

        print(f"[SUCCESS] Scraped {len(cases)} test cases. Saved to reference_test_cases.json")
        print("[PREVIEW] First 5 cases:")
        for case in cases[:5]:
            print(f"   - {case['raw_title']}")
    else:
        print("[FAILED] Scraping did not return enough cases. Please use the fallback JSON below.")