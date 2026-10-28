import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_search_product():
    # Step 1: Send POST request with search_product parameter
    response = requests.post(f"{BASE_URL}/api/searchProduct", data={"search_product": "tshirt"})
    
    # Step 2: Verify response code is 200
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    # Step 3: Verify response contains products matching the search
    json_data = response.json()
    assert "products" in json_data, "Response does not contain 'products' key"
    products = json_data["products"]
    assert len(products) > 0, "No products found in response"
    
    # Verify each product contains the search term in name or category
    for product in products:
        product_name = product.get("name", "").lower()
        category = product.get("category", {}).get("category", "").lower() if isinstance(product.get("category"), dict) else ""
        assert "tshirt" in product_name or "tshirt" in category, f"Product '{product.get('name')}' does not match search term"