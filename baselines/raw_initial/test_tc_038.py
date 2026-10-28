import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_verify_login_invalid_credentials():
    # Step 1: Send POST request with invalid credentials
    url = f"{BASE_URL}/api/verifyLogin"
    data = {
        "email": "wrongTest@example.com",
        "password": "wrongpass"
    }
    response = requests.post(url, data=data)
    
    
    # Step 2: Verify response message indicates 'User not found!'
    response_json = response.json()
    assert response_json.get("responseCode") == 404, f"Expected status code 404, got {response.status_code}"

    assert response_json.get("message") == "User not found!", f"Expected message 'User not found!', got {response_json.get('message')}"