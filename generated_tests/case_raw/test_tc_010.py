import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_search_product_with_invalid_keyword(page):
    print("Starting TC_010: Verify search product with invalid keyword")
    
    # Step 1: Navigate to the site
    print("Step 1: Navigating to automationexercise.com")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    
    # Step 2: Click on 'Products' button
    print("Step 2: Clicking on 'Products' button")
    page.locator("a[href='/products']").click()
    
    # Step 3: Enter invalid keyword in search box
    print("Step 3: Entering 'NonExistentProduct' in search box")
    search_box = page.locator("#search_product")
    search_box.fill("NonExistentProduct")
    
    # Step 4: Click 'Search' button
    print("Step 4: Clicking 'Search' button")
    page.locator("#submit_search").click()
    
    # Step 5: Verify no products found message
    print("Step 5: Verifying 'No products found' message is displayed")
    no_products_message = page.locator("text=No products found")
    expect(no_products_message).to_be_visible()
    
    print("TC_010 passed: 'No products found' message is displayed")