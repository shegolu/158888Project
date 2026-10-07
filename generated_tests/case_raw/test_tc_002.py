import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_user_registration_with_existing_email(page: Page):
    print("Starting TC_002: Verify user registration with existing email")
    
    # Step 0: Navigate to the site
    print("Navigating to automationexercise.com")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    
    # Step 1: Click on 'Signup / Login' button
    print("Step 1: Clicking on 'Signup / Login' button")
    page.locator("a[href='/login']").click()
    
    # Step 2: Enter name and existing email
    print("Step 2: Entering name 'NewUser' and email 'existing@example.com'")
    page.locator("input[data-qa='signup-name']").fill("NewUser")
    page.locator("input[data-qa='signup-email']").fill("existing@example.com")
    
    # Step 3: Click 'Signup' button
    print("Step 3: Clicking 'Signup' button")
    page.locator("button[data-qa='signup-button']").click()
    
    # Step 4: Observe the error message
    print("Step 4: Checking for error message")
    error_message = page.locator("p", has_text="Email Address already exist!")
    expect(error_message).to_be_visible()
    print("Test passed: Error message 'Email Address already exist!' is displayed")