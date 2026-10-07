import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_subscription_in_home_page(page):
    print("Starting TC_011: Verify subscription in home page")
    
    # Precondition: Navigate to the site
    print("Step 0: Navigating to automationexercise.com")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    
    # Step 1: Scroll to the bottom of the home page
    print("Step 1: Scrolling to the bottom of the home page")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    # Step 2: Enter email in subscription input
    print("Step 2: Entering email in subscription input")
    email_input = page.locator("#susbscribe_email")
    email_input.fill("subscriber@example.com")
    
    # Step 3: Click the subscribe arrow button
    print("Step 3: Clicking the subscribe arrow button")
    subscribe_button = page.locator("#subscribe")
    subscribe_button.click()
    
    # Step 4: Verify success message
    print("Step 4: Verifying success message")
    success_message = page.locator(".alert-success")
    expect(success_message).to_be_visible()
    expect(success_message).to_contain_text("You have been successfully subscribed!")
    
    print("TC_011 completed successfully")