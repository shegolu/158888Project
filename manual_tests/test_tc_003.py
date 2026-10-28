import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_user_login_with_correct_credentials(page):
    print("Starting TC_003: Verify user login with correct credentials")
    
    # Step 1: Navigate to the site and click on 'Signup / Login'
    print("Step 1: Navigating to automationexercise.com and clicking 'Signup / Login'")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    page.locator("a[href='/login']").click()
    
    # Step 2: Enter email and password
    print("Step 2: Entering email and password")
    page.locator("input[data-qa='login-email']").fill("testuserfix@example.com")
    page.locator("input[data-qa='login-password']").fill("Test@123")
    
    # Step 3: Click 'Login' button
    print("Step 3: Clicking 'Login' button")
    page.locator("button[data-qa='login-button']").click()
    
    # Step 4: Verify 'Logged in as TestUser' is visible
    print("Step 4: Verifying 'Logged in as TestUser' is visible")
    logged_in_text = page.locator("li:has-text('Logged in as') a")
    expect(logged_in_text).to_be_visible()
    expect(logged_in_text).to_contain_text("Test")
    
    print("TC_003 Passed: User logged in successfully and 'Logged in as TestUser' is displayed")