import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_verify_get_all_products_list():
    # Step 1: Send a GET request to the products list endpoint
    response = requests.get(f"{BASE_URL}/api/productsList")
    
    # Step 2: Verify the response code is 200
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    
    # Step 3: Verify the response contains a list of products
    data = response.json()
    assert "products" in data, "Response does not contain 'products' key"
    assert isinstance(data["products"], list), "Products field is not a list"
    assert len(data["products"]) > 0, "Products list is empty"