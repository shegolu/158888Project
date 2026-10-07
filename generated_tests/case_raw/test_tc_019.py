import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_place_order_login_before_checkout(page: Page):
    print("Starting TC_019: Verify place order with login before checkout")
    
    # Precondition: Navigate to the site
    print("Step 0: Navigating to automationexercise.com")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    expect(page).to_have_title("Automation Exercise")
    
    # Add a product to cart (assuming first product)
    print("Adding a product to cart")
    page.locator(".features_items .product-image-wrapper").first.locator(".choose").click()
    page.locator("button[type='button']").filter(has_text="Add to cart").click()
    page.locator(".modal-footer .btn-success").click()  # Continue shopping
    
    # Step 1: Login with valid credentials
    print("Step 1: Logging in with valid credentials")
    page.locator("a[href='/login']").click()
    page.locator("input[data-qa='login-email']").fill("testuserfix@example.com")
    page.locator("input[data-qa='login-password']").fill("Test@123")
    page.locator("button[data-qa='login-button']").click()
    expect(page.locator("a[href='/logout']")).to_be_visible()
    print("Login successful")
    
    # Step 2: Click on 'Cart' button
    print("Step 2: Clicking on Cart button")
    page.locator("a[href='/view_cart']").click()
    expect(page.locator("li.active")).to_have_text("Shopping Cart")
    
    # Step 3: Click 'Proceed To Checkout' button
    print("Step 3: Clicking Proceed To Checkout")
    page.locator("a.btn.btn-default.check_out").click()
    expect(page.locator("li.active")).to_have_text("Checkout")
    
    # Step 4: Fill in delivery address and place order
    print("Step 4: Filling delivery address and placing order")
    # Assuming address is pre-filled from account, but we can verify
    expect(page.locator("#address_delivery .address_firstname")).to_contain_text("Updated User")
    page.locator("a.btn.btn-default.check_out").click()  # Place Order button
    
    # Step 5: Enter payment details and confirm order
    print("Step 5: Entering payment details")
    page.locator("input[name='name_on_card']").fill("Updated User")
    page.locator("input[name='card_number']").fill("1234567890123456")
    page.locator("input[name='cvc']").fill("123")
    page.locator("input[name='expiry_month']").fill("12")
    page.locator("input[name='expiry_year']").fill("2025")
    page.locator("button[data-qa='pay-button']").click()
    
    # Step 6: Verify order success message
    print("Step 6: Verifying order success message")
    expect(page.get_by_text("Congratulations! Your order has been confirmed!")).to_be_visible()
    print("Order placed successfully")
    
    print("TC_019 completed successfully")