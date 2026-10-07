import requests

BASE_URL = "https://automationexercise.com"

def test_get_user_detail():
    response = requests.get("https://automationexercise.com/api/getUserDetailByEmail?email=testuserfix@example.com")
    data = response.json()
    assert data.get("responseCode") == 200
    assert "user" in data
    assert data["user"]["email"] == "testuserfix@example.com"