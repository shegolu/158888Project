import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_remove_product_from_cart(page: Page):
    print("Starting TC_016: Verify remove product from cart")
    
    # Navigate to the site
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    print("Navigated to automationexercise.com")
    
    # Add a product to the cart (precondition)
    # Assuming the first product on the homepage is visible and has an "Add to cart" button
    page.locator(".productinfo.text-center a[data-product-id]").first.click()
    print("Clicked 'Add to cart' on first product")
    
    # Click "Continue Shopping" to stay on the page
    page.locator("button.close-modal").click()
    print("Clicked 'Continue Shopping'")
    
    # Step 1: Click on 'Cart' button
    page.locator("li a[href='/view_cart']").click()
    print("Step 1: Clicked on 'Cart' button")
    
    # Verify product is in cart before removal
    expect(page.locator("#cart_info_table")).to_be_visible()
    expect(page.locator("#cart_info_table tbody tr")).to_have_count(1)
    print("Product is present in cart")
    
    # Step 2: Click the 'X' button to remove the product
    page.locator(".cart_quantity_delete").click()
    print("Step 2: Clicked the 'X' button to remove the product")
    
    # Step 3: Verify that the cart is empty
    # The cart page shows a message "Cart is empty!" when no items
    expect(page.locator("text=Cart is empty!")).to_be_visible()
    print("Step 3: Verified cart is empty")
    
    print("TC_016 completed successfully")