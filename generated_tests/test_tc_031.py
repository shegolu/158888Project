import requests
import pytest

BASE_URL = "https://automationexercise.com"

def test_verify_get_all_brands_list():
    response = requests.get(f"{BASE_URL}/api/brandsList")
    assert response.status_code == 200
    data = response.json()
    assert "brands" in data
    assert isinstance(data["brands"], list)
    assert len(data["brands"]) > 0