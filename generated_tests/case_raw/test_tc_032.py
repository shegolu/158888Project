import requests

BASE_URL = "https://automationexercise.com"


def test_brands_list_put_method_not_allowed():
    response = requests.put(f"{BASE_URL}/api/brandsList", timeout=30)
    body = response.json()
    assert body["responseCode"] == 405
    assert body["message"] == "This request method is not supported."
