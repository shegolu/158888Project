import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def browser_context(page: Page):
    # Setup: navigate to the base URL
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    yield page
    # Teardown: close the page (handled by Playwright fixture)

def test_verify_search_products_and_cart_after_login(browser_context: Page):
    page = browser_context
    print("Starting TC_022: Verify search products and verify cart after login")
    
    # Step 1: Search for a product and add it to cart
    print("Step 1: Searching for a product and adding to cart")
    # Assuming a search bar exists; use a common product name like "dress"
    page.locator('input[name="search"]').fill("dress")
    page.locator('button[type="submit"]').click()
    # Wait for search results and click "Add to cart" on the first product
    # Using a generic selector; adjust based on actual page structure
    first_product_add_to_cart = page.locator('.productinfo .btn-add-to-cart').first
    first_product_add_to_cart.click()
    # Handle modal if appears (e.g., "Added!" popup) - click continue shopping
    page.locator('.modal-footer .btn-success').click()  # Continue Shopping button
    
    # Step 2: Click 'Cart' and verify the product is in the cart
    print("Step 2: Clicking Cart and verifying product")
    page.locator('a[href="/view_cart"]').click()
    cart_items = page.locator('.cart_info tbody tr')
    expect(cart_items).to_have_count(1)  # Assuming one item added
    # Verify product name appears in cart
    expect(page.locator('.cart_description a')).to_contain_text("dress")
    print("Product verified in cart before login")
    
    # Step 3: Logout
    print("Step 3: Logging out")
    page.locator('a[href="/logout"]').click()
    # Verify logged out (e.g., login page visible)
    expect(page.locator('a[href="/login"]')).to_be_visible()
    
    # Step 4: Login with valid credentials
    print("Step 4: Logging in with valid credentials")
    # Assuming valid credentials; replace with actual test data
    page.locator('a[href="/login"]').click()
    page.locator('input[data-qa="login-email"]').fill("testuser@example.com")
    page.locator('input[data-qa="login-password"]').fill("password123")
    page.locator('button[data-qa="login-button"]').click()
    # Verify login successful (e.g., logout link visible)
    expect(page.locator('a[href="/logout"]')).to_be_visible()
    
    # Step 5: Click 'Cart' and verify the product is still in the cart
    print("Step 5: Clicking Cart after login and verifying product")
    page.locator('a[href="/view_cart"]').click()
    cart_items_after_login = page.locator('.cart_info tbody tr')
    expect(cart_items_after_login).to_have_count(1)
    expect(page.locator('.cart_description a')).to_contain_text("dress")
    print("Product verified in cart after login")
    
    print("TC_022 completed successfully")