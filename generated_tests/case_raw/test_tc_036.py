import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_verify_login_without_email():
    # Step 1: Send POST request with only password parameter
    response = requests.post(f"{BASE_URL}/api/verifyLogin", data={"password": "testpass"})
    
    
    # Step 2: Verify response message
    json_response = response.json()
    assert json_response.get("responseCode") == 400, f"Expected status code 400, got {response.status_code}"

    assert json_response.get("message") == "Bad request, email or password parameter is missing in POST request.", f"Unexpected message: {json_response}"