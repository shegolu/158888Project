import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_search_product_without_parameter():
    # Step 1: Send POST request without parameters
    response = requests.post(f"{BASE_URL}/api/searchProduct")
        
    # Step 2: Verify response message
    response_data = response.json()
    assert response_data.get("responseCode") == 400, f"Expected status code 400, got {response.status_code}"

    assert response_data.get("message") == "Bad request, search_product parameter is missing in POST request.", \
        f"Unexpected message: {response_data.get('message')}"