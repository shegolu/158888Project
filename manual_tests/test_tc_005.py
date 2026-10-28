import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_user_logout_functionality(page: Page):
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