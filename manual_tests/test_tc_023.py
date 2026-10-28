import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_add_review_on_product(page: Page):
    print("Starting TC_023: Verify add review on product")
    
    # Step 1: Navigate to the site and click on 'Products' button
    print("Step 1: Navigating to automationexercise.com and clicking 'Products'")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    page.locator("a[href='/products']").click()
    
    # Step 2: Click 'View Product' for the first product
    print("Step 2: Clicking 'View Product' for the first product")
    page.locator(".features_items .product-image-wrapper").first.locator("a[href*='/product_details']").click()
    
    # Step 3: Scroll to the review section
    print("Step 3: Scrolling to the review section")
    review_section = page.get_by_text("Write Your Review")
    review_section.scroll_into_view_if_needed()
    
    # Step 4: Fill in the review form
    print("Step 4: Filling in review form with name, email, and review")
    page.locator("#name").fill("TestUser")
    page.locator("#email").fill("testuser@example.com")
    page.locator("#review").fill("Great product!")
    
    # Step 5: Click 'Submit' button
    print("Step 5: Clicking 'Submit' button")
    page.locator("#button-review").click()
    
    # Step 6: Verify success message
    print("Step 6: Verifying success message")
    success_message = page.get_by_text("Thank you for your review.")
    expect(success_message).to_be_visible()
    expect(success_message).to_contain_text("Thank you for your review.")
    
    print("TC_023 completed successfully")