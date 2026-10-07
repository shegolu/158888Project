import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_verify_login_valid_credentials():
    url = f"{BASE_URL}/api/verifyLogin"
    data = {
        "email": "testuserfix@example.com",
        "password": "Test@123"
    }
    response = requests.post(url, data=data)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response.get("message") == "User exists!"