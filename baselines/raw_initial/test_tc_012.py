import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_subscription_in_cart_page(page: Page):
    print("Starting TC_012: Verify subscription in cart page")
    
    # Step 1: Navigate to the site and click on 'Cart' button
    print("Step 1: Navigating to automationexercise.com and clicking Cart button")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    page.locator("a[href='/view_cart']").click()
    expect(page).to_have_url("https://automationexercise.com/view_cart")
    print("Cart page loaded")
    
    # Step 2: Scroll to the bottom of the cart page
    print("Step 2: Scrolling to the bottom of the cart page")
    page.locator("#footer").scroll_into_view_if_needed()
    
    # Step 3: Enter email in subscription input
    print("Step 3: Entering email in subscription input")
    subscription_input = page.locator("#susbscribe_email")
    subscription_input.fill("cartsubscriber@example.com")
    
    # Step 4: Click the subscribe arrow button
    print("Step 4: Clicking subscribe arrow button")
    page.locator("#subscribe").click()
    
    # Step 5: Verify success message
    print("Step 5: Verifying success message")
    success_message = page.locator("#success-subscribe")
    expect(success_message).to_be_visible()
    expect(success_message).to_contain_text("You have been successfully subscribed!")
    print("Success message verified: 'You have been successfully subscribed!'")
    
    print("TC_012 completed successfully")