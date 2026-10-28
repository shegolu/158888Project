import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_product_quantity_in_cart(page: Page):
    print("Starting TC_015: Verify product quantity in cart")
    
    # Step 1: Navigate to the site and click on 'Products' button
    print("Step 1: Navigating to automationexercise.com and clicking 'Products'")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    page.locator("a[href='/products']").click()
    expect(page).to_have_url("https://automationexercise.com/products")
    
    # Step 2: Click 'View Product' for the first product
    print("Step 2: Clicking 'View Product' for the first product")
    page.locator(".features_items .product-image-wrapper").first.locator("a[href*='/product_details/']").click()
    expect(page.locator(".product-information")).to_be_visible()
    
    # Step 3: Increase quantity to 4
    print("Step 3: Setting quantity to 4")
    quantity_input = page.locator("#quantity")
    quantity_input.fill("4")
    # Verify the value is set correctly
    expect(quantity_input).to_have_value("4")
    
    # Step 4: Click 'Add to cart' button
    print("Step 4: Clicking 'Add to cart'")
    page.locator("button.btn-default.cart").click()
    # Wait for the modal to appear
    expect(page.locator(".modal-content")).to_be_visible()
    
    # Step 5: Click 'View Cart' button
    print("Step 5: Clicking 'View Cart'")
    page.locator(".modal-content a[href='/view_cart']").click()
    expect(page).to_have_url("https://automationexercise.com/view_cart")
    
    # Step 6: Verify that the quantity is 4
    print("Step 6: Verifying cart quantity is 4")
    cart_quantity = page.locator(".cart_quantity")
    expect(cart_quantity).to_have_text("4")
    
    print("TC_015 passed: Product quantity in cart is 4")