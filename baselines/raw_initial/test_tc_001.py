import pytest
from playwright.sync_api import Page, expect
import time

from generated_tests.test_tc_004 import page

@pytest.fixture(scope="function")
def browser_context(page: Page):
    print("Setting up browser and navigating to the site")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    yield page
    print("Tearing down browser")

def test_verify_user_registration_with_valid_data(browser_context: Page):
    page = browser_context
    print("Step 1: Click on 'Signup / Login' button")
    page.locator("a[href='/login']").click()
    
    print("Step 2: Enter name 'TestUser' and email address 'testuser@example.com'")
    page.locator("input[data-qa='signup-name']").fill("TestUser")
    page.locator("input[data-qa='signup-email']").fill("testuser@example.com")    
    print("Step 3: Click 'Signup' button")
    page.locator("button[data-qa='signup-button']").click()
    
    print("Step 4: Fill in account details: Title, Password 'Test@123', Date of Birth")
    page.locator("#id_gender1").check()
    page.locator("input[data-qa='password']").fill("Test@123")
    page.locator("select[data-qa='days']").select_option("10")
    page.locator("select[data-qa='months']").select_option("5")
    page.locator("select[data-qa='years']").select_option("1990")
    
    print("Step 5: Check 'Sign up for our newsletter!' checkbox")
    page.locator("#newsletter").check()
    
    print("Step 6: Fill in Address Information")
    page.locator("input[data-qa='first_name']").fill("Test")
    page.locator("input[data-qa='last_name']").fill("User")
    page.locator("input[data-qa='company']").fill("Test Company")
    page.locator("input[data-qa='address']").fill("123 Test Street")
    page.locator("select[data-qa='country']").select_option("United States")
    page.locator("input[data-qa='state']").fill("California")
    page.locator("input[data-qa='city']").fill("Los Angeles")
    page.locator("input[data-qa='zipcode']").fill("90001")
    page.locator("input[data-qa='mobile_number']").fill("1234567890")
    
    print("Step 7: Click 'Create Account' button")
    page.locator("button[data-qa='create-account']").click()
    
    print("Step 8: Verify 'ACCOUNT CREATED!' is visible")
    expect(page.locator("h2[data-qa='account-created']")).to_be_visible()
    expect(page.locator("h2[data-qa='account-created']")).to_contain_text("ACCOUNT CREATED!",ignore_case=True)
    
    print("Step 9: Click 'Continue' button")
    page.locator("a[data-qa='continue-button']").click()
    
    print("Step 10: Verify logged in as 'TestUser'")
    expect(page.locator("a:has-text('Logged in as')")).to_contain_text("TestUser")
    
    print("Test completed successfully")