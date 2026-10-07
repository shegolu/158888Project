import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_add_to_cart_from_recommended_items(page):
    print("Starting TC_024: Verify add to cart from recommended items")
    
    # Step 1: Navigate to the home page
    print("Step 1: Navigating to home page")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    
    # Step 2: Scroll to the bottom of the home page
    print("Step 2: Scrolling to the bottom of the home page")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    # Step 3: Verify that 'RECOMMENDED ITEMS' are visible
    print("Step 3: Verifying 'RECOMMENDED ITEMS' section is visible")
    recommended_items_header = page.locator("h2:has-text('recommended items')")
    expect(recommended_items_header).to_be_visible()
    print("'RECOMMENDED ITEMS' section is visible")
    
    # Step 4: Click 'Add to cart' on a recommended product
    print("Step 4: Clicking 'Add to cart' on a recommended product")
    # Find the first recommended product's add to cart button
    # The recommended items section typically has a carousel, we'll target the first product
    add_to_cart_button = page.locator("#recommended-item-carousel .item.active .add-to-cart").first    
    expect(add_to_cart_button).to_be_visible()
    add_to_cart_button.click()
    print("Clicked 'Add to cart' on the first recommended product")
    
    # Step 5: Click 'View Cart' button
    print("Step 5: Clicking 'View Cart' button")
    view_cart_button = page.locator("a:has-text('View Cart')")
    expect(view_cart_button).to_be_visible()
    view_cart_button.click()
    print("Clicked 'View Cart' button")
    
    # Step 6: Verify that the product is in the cart
    print("Step 6: Verifying the product is in the cart")
    # Check that the cart page is loaded and contains at least one product
    cart_page = page.locator("#cart_items")
    expect(cart_page).to_be_visible()
    
    # Verify there is at least one product in the cart
    cart_products = page.locator("#cart_info_table tbody tr")
    expect(cart_products.first).to_be_visible()
    print("Product is successfully added to the cart")
    
    print("TC_024 completed successfully")