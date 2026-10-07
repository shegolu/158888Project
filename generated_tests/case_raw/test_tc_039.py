import requests

BASE_URL = "https://automationexercise.com"

def test_create_account():
    response = requests.post(
        f"{BASE_URL}/api/createAccount",
        data={    "name": "NewUser",
        "email": "newuserTest2026@example.com",
        "password": "Test@123",
        "title": "Mr",
        "birth_date": "01",
        "birth_month": "January",
        "birth_year": "1990",
        "firstname": "New",
        "lastname": "User",
        "company": "TestCompany",
        "address1": "123 Test St",
        "address2": "Suite 1",
        "country": "United States",
        "zipcode": "12345",
        "state": "California",
        "city": "Los Angeles",
        "mobile_number": "1234567890"
    }
    )
    assert response.json().get("responseCode") == 201
    assert response.json().get("message") == "User created!"