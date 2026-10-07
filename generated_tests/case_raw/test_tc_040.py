import requests

BASE_URL = "https://automationexercise.com"

def test_delete_account():
    response= requests.delete(f"{BASE_URL}/api/deleteAccount", data={"email": "newuserTest2026@example.com", "password": "Test@123"})
    assert response.json().get("responseCode") == 200
    assert response.json().get("message") == "Account deleted!"