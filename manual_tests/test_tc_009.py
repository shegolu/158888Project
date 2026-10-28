import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_search_product_with_valid_keyword(page):
    print("Starting TC_009: Verify search product with valid keyword")
    
    # Step 1: Navigate to the site
    print("Step 1: Navigating to automationexercise.com")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    
    # Step 2: Click on 'Products' button
    print("Step 2: Clicking on 'Products' button")
    page.locator("a[href='/products']").click()
    
    # Step 3: Enter 'T-Shirt' in the search box
    print("Step 3: Entering 'T-Shirt' in the search box")
    search_box = page.locator("#search_product")
    search_box.fill("T-Shirt")
    
    # Step 4: Click 'Search' button
    print("Step 4: Clicking 'Search' button")
    page.locator("#submit_search").click()
    
    # Step 5: Verify that the search results are displayed
    print("Step 5: Verifying search results are displayed")
    search_results = page.locator(".features_items")
    expect(search_results).to_be_visible()
    
    # Step 6: Verify that all products contain 'T-Shirt' in their name
    print("Step 6: Verifying all products contain 'T-Shirt' in their name")
    product_names = page.locator(".productinfo p")
    count = product_names.count()
    assert count > 0, "No products found in search results"
    
    for i in range(count):
        product_name = product_names.nth(i).inner_text()
        assert "T-Shirt" in product_name, f"Product '{product_name}' does not contain 'T-Shirt'"
    
    print("TC_009 completed successfully: All products contain 'T-Shirt'")