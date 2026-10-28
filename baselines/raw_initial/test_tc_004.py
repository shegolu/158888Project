import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_incorrect_login(page):
    print("Starting TC_004: Verify user login with incorrect credentials")
    
    # Step 1: Navigate to the site and click on 'Signup / Login'
    print("Step 1: Navigating to automationexercise.com and clicking 'Signup / Login'")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    page.locator("a[href='/login']").click()
    
    # Step 2: Enter incorrect email and password
    print("Step 2: Entering incorrect email and password")
    page.locator("input[data-qa='login-email']").fill("wronguser@example.com")
    page.locator("input[data-qa='login-password']").fill("WrongPass123")
    
    # Step 3: Click 'Login' button
    print("Step 3: Clicking 'Login' button")
    page.locator("button[data-qa='login-button']").click()
    
    # Step 4: Verify error message is displayed
    print("Step 4: Verifying error message")
    error_message = page.locator("p[style*='color: red']")
    expect(error_message).to_be_visible()
    expect(error_message).to_contain_text("Your email or password is incorrect!")
    
    print("TC_004 passed: Error message displayed correctly")