import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_view_brand_products(page):
    print("Starting TC_021: Verify view brand products")
    
    # Step 1: Navigate to the site
    print("Step 1: Navigating to automationexercise.com")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    
    # Step 2: Scroll to the left sidebar (brands section)
    print("Step 2: Scrolling to the left sidebar")
    # The brands section is typically in the left sidebar, we can scroll to it
    brands_heading = page.locator("div.brands_products h2")
    brands_heading.scroll_into_view_if_needed()
    expect(brands_heading).to_be_visible()
    print("Left sidebar with brands is visible")
    
    # Step 3: Click on the 'Polo' brand
    print("Step 3: Clicking on the 'Polo' brand")
    polo_link = page.locator("div.brands_products a", has_text="Polo")
    polo_link.click()
    
    # Step 4: Verify that brand products are displayed
    print("Step 4: Verifying brand products are displayed")
    # Check that the page shows products for the selected brand
    # The URL should contain brand_products/Polo
    expect(page).to_have_url("https://automationexercise.com/brand_products/Polo")
    
    # Verify the brand title is displayed
    brand_title = page.locator("h2.title.text-center")
    expect(brand_title).to_contain_text("Brand - Polo")
    
    # Verify that at least one product is visible
    products = page.locator("div.productinfo")
    expect(products.first).to_be_visible()
    
    # Count the number of products displayed
    product_count = products.count()
    print(f"Number of Polo products displayed: {product_count}")
    assert product_count > 0, "No products found for the Polo brand"
    
    print("TC_021 completed successfully: Brand products are displayed")