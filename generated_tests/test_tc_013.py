import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_add_single_product_to_cart(page: Page):
    print("Starting TC_013: Verify add single product to cart")
    
    # Step 1: Navigate to the site and click on 'Products' button
    print("Step 1: Navigating to automationexercise.com and clicking Products button")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)

    page.locator("a[href='/products']").click()
    expect(page).to_have_url("https://automationexercise.com/products")
    print("Products page loaded")
    
    # Step 2: Hover over the first product and click 'Add to cart'
    print("Step 2: Hovering over first product and clicking Add to cart")
    first_product = page.locator(".features_items .product-image-wrapper").first
    add_button = first_product.locator(".productinfo .add-to-cart") 
    add_button.click()
    page.wait_for_timeout(2000)  # Wait for 2 seconds to ensure the action is completed
    print("Add to cart clicked")
    
    # Step 3: Click 'View Cart' button
    print("Step 3: Clicking View Cart button")
    page.locator("ul.navbar-nav a[href='/view_cart']").click()
    expect(page).to_have_url("https://automationexercise.com/view_cart")
    print("Cart page loaded")
    
    # Step 4: Verify that the product is in the cart
    print("Step 4: Verifying product is in cart")
    cart_items = page.locator("#cart_info_table tbody tr")
    expect(cart_items).to_have_count(1)
    expect(cart_items.first).to_contain_text("Blue Top")
    print("Product verified in cart")
    
    print("TC_013 completed successfully")