import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_verify_post_to_all_products_list_api_method_not_allowed():
    # Step 1: Add a browser-like User-Agent to bypass Cloudflare protection
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Send a POST request, and set a timeout to prevent hanging
    response = requests.post(f"{BASE_URL}/api/productsList", headers=headers, timeout=10)

    # Step 2: Parse the JSON response (Important!!!)
    data = response.json()

    # Step 3: Corrected assertions
    # Because the HTTP status code is 200, the business responseCode is the actual 405
    assert data["responseCode"] == 405, f"Expected responseCode 405, but got {data['responseCode']}"
    assert data["message"] == "This request method is not supported."
    
    print("Test passed!")