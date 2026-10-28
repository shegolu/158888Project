import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def browser_context(page: Page):
    """Setup browser context and navigate to the base URL."""
    print("Setting up browser and navigating to automationexercise.com")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    yield page
    print("Tearing down browser")

def test_add_multiple_products_to_cart(browser_context: Page):
    """TC_014: Verify add multiple products to cart."""
    page = browser_context
    print("Step 1: Click on 'Products' button")
    page.locator("a[href='/products']").click()
    expect(page).to_have_url("https://automationexercise.com/products")
    print("Products page loaded")

    print("Step 2: Add the first product to cart")
    # Assuming first product is the first product card; using its 'Add to cart' button
    first_product_add = page.locator(".productinfo.text-center a.btn.btn-default.add-to-cart").first
    first_product_add.click()
    print("First product added to cart")

    print("Step 3: Continue shopping and add the second product to cart")
    # Click 'Continue Shopping' button in modal
    page.locator("button.close-modal").click()  # or use .btn-success.close-modal depending on actual DOM
    # Wait for modal to close and then add second product
    second_product_add = page.locator(".productinfo.text-center a.btn.btn-default.add-to-cart").nth(1)
    second_product_add.click()
    print("Second product added to cart")

    print("Step 4: Click 'View Cart' button")
    page.locator("a[href='/view_cart']").first.click()
    expect(page).to_have_url("https://automationexercise.com/view_cart")
    print("Cart page loaded")

    print("Step 5: Verify that both products are in the cart")
    # Assuming cart items are in a table with class 'cart_product' or similar
    cart_items = page.locator("#cart_info_table tbody tr")  # adjust selector based on actual page structure
    expect(cart_items).to_have_count(2)
    # Optionally verify product names are present
    expect(page.locator("td.cart_description h4 a")).to_have_count(2)
    print("Both products verified in cart")

    print("Test TC_014 passed")