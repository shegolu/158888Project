import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_verify_login_delete_method_not_allowed():
    # Step 1: Send a DELETE request to the verifyLogin endpoint
    response = requests.delete(f"{BASE_URL}/api/verifyLogin")

    
    # Step 2: Verify the response message indicates method not allowed
    response_data = response.json()
    assert response_data.get("responseCode") == 405, f"Expected status code 405, but got {response.status_code}"
    assert "message" in response_data, "Response JSON does not contain 'message' field"
    assert response_data["message"] == "This request method is not supported.", f"Unexpected message: {response_data['message']}"