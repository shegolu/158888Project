import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def browser_context(page: Page):
    # Navigate to the base URL
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    # Assume user is already logged in (precondition)
    # For demonstration, we'll just proceed to logout
    yield page
    # Teardown: close page (handled by Playwright fixture)

def test_verify_user_logout_functionality(browser_context: Page):
    page = browser_context
    print("Starting TC_005: Verify user logout functionality")
    
    # Step 1: Click on 'Logout' button
    print("Step 1: Clicking on 'Logout' button")
    logout_button = page.locator("a[href='/logout']")
    expect(logout_button).to_be_visible()
    logout_button.click()
    
    # Step 2: Verify that the user is navigated to the login page
    print("Step 2: Verifying navigation to login page")
    expect(page).to_have_url("https://automationexercise.com/login")
    
    # Step 3: Verify that 'Login to your account' is visible
    print("Step 3: Verifying 'Login to your account' is visible")
    login_header = page.locator("h2:has-text('Login to your account')")
    expect(login_header).to_be_visible()
    
    print("TC_005 completed successfully: User is logged out and redirected to login page")