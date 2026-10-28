import requests

BASE_URL = "https://automationexercise.com"

def test_update_account():
    response = requests.put(f"{BASE_URL}/api/updateAccount", data={
    "name": "Test",
    "email": "testuserfix@example.com",
    "password": "Test@123",
    "title": "Mr",
    "birth_date": "01",
    "birth_month": "January",
    "birth_year": "1990",
    "firstname": "Updated",
    "lastname": "User",
    "company": "NewCompany",
    "address1": "456 New St",
    "address2": "Suite 2",
    "country": "United States",
    "zipcode": "54321",
    "state": "New York",
    "city": "New York",
    "mobile_number": "0987654321"
    })
    assert response.json().get("responseCode") == 200
    assert response.json().get("message") == "User updated!"