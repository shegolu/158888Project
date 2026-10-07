import requests

BASE_URL = "https://automationexercise.com"

def test_brands_list_put_method_not_allowed():
    response = requests.put(f"{BASE_URL}/api/brandsList")
    assert response.status_code == 405
    assert response.json()["responseCode"] == 405
    assert response.json()["message"] == "This request method is not supported."