import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_view_category_products(page):
    print("Starting TC_020: Verify view category products")
    
    # Step 0: Navigate to the site
    print("Step 0: Navigating to automationexercise.com")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    expect(page).to_have_title("Automation Exercise")
    
    # Step 1: Scroll to the left sidebar
    print("Step 1: Scrolling to the left sidebar")
    page.locator(".left-sidebar").scroll_into_view_if_needed()
    expect(page.locator(".left-sidebar")).to_be_visible()
    
    # Step 2: Click on 'Women' category
    print("Step 2: Clicking on 'Women' category")
    women_category = page.locator("a[href='#Women']")
    women_category.click()
    # Wait for the subcategory to be visible (auto-wait)
    expect(page.locator("#Women .panel-body")).to_be_visible()
    
    # Step 3: Click on 'Dress' subcategory
    print("Step 3: Clicking on 'Dress' subcategory")
    dress_link = page.locator("#Women .panel-body a[href*='category_products']").filter(has_text="Dress")
    dress_link.click()
    
    # Step 4: Verify category products are displayed
    print("Step 4: Verifying category products are displayed")
    # Check that the title contains 'Women - Dress Products'
    expect(page.locator(".title")).to_contain_text("Women - Dress Products")
    # Verify product items are visible
    products = page.locator(".features_items .product-image-wrapper")
    expect(products.first).to_be_visible()
    product_count = products.count()
    print(f"Verified {product_count} products displayed for Women - Dress category")
    
    print("TC_020 completed successfully")