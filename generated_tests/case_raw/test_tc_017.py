import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_place_order_register_while_checkout(page: Page):
    print("Starting TC_017: Verify place order - register while checkout")
    
    # Precondition: Navigate to the site and add a product to cart
    print("Step 0: Navigating to automationexercise.com and adding product to cart")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    # Assuming first product's "Add to cart" button is visible; adjust selector if needed
    page.locator(".productinfo a[data-product-id]").first.click()
    page.locator(".modal-footer .btn-success").click()  # Click "Continue Shopping" in modal
    
    # Step 1: Click on 'Cart' button
    print("Step 1: Clicking on Cart button")
    page.locator("a[href='/view_cart']").click()
    expect(page.locator("h2:has-text('Shopping Cart')")).to_be_visible()
    
    # Step 2: Click 'Proceed To Checkout' button
    print("Step 2: Clicking Proceed To Checkout")
    page.locator("a.check_out").click()
    expect(page.locator("h2:has-text('Checkout')")).to_be_visible()
    
    # Step 3: Click 'Register / Login' button
    print("Step 3: Clicking Register / Login button")
    page.locator("a[href='/login']").click()
    expect(page.locator("h2:has-text('Login to your account')")).to_be_visible()
    
    # Step 4: Register a new account with valid details
    print("Step 4: Registering a new account")
    # Click on "Signup" link (assuming we are on login page)
    page.locator("a[href='/signup']").click()
    expect(page.locator("h2:has-text('New User Signup!')")).to_be_visible()
    
    # Fill signup form
    import random
    email = f"testuser{random.randint(1000,9999)}@example.com"
    page.locator("input[data-qa='signup-name']").fill("Test User")
    page.locator("input[data-qa='signup-email']").fill(email)
    page.locator("button[data-qa='signup-button']").click()
    
    # Fill account information
    expect(page.locator("h2:has-text('Enter Account Information')")).to_be_visible()
    page.locator("#id_gender1").check()  # Mr.
    page.locator("input[data-qa='password']").fill("password123")
    page.locator("select[data-qa='days']").select_option("10")
    page.locator("select[data-qa='months']").select_option("5")
    page.locator("select[data-qa='years']").select_option("1990")
    page.locator("#newsletter").check()
    page.locator("#optin").check()
    
    # Address Information
    page.locator("input[data-qa='first_name']").fill("Test")
    page.locator("input[data-qa='last_name']").fill("User")
    page.locator("input[data-qa='company']").fill("Test Company")
    page.locator("input[data-qa='address']").fill("123 Test Street")
    page.locator("input[data-qa='address2']").fill("Apt 4B")
    page.locator("select[data-qa='country']").select_option("United States")
    page.locator("input[data-qa='state']").fill("California")
    page.locator("input[data-qa='city']").fill("Los Angeles")
    page.locator("input[data-qa='zipcode']").fill("90001")
    page.locator("input[data-qa='mobile_number']").fill("1234567890")
    page.locator("button[data-qa='create-account']").click()
    
    # Verify account created and continue
    expect(page.locator("h2:has-text('Account Created!')")).to_be_visible()
    page.locator("a[data-qa='continue-button']").click()
    
    # Step 5: Click 'Proceed To Checkout' button (now logged in)
    print("Step 5: Clicking Proceed To Checkout after login")
    page.locator("a[href='/view_cart']").click()
    page.locator("a.check_out").click()
    expect(page.locator("h2:has-text('Checkout')")).to_be_visible()
    
    # Step 6: Fill in the delivery address and place order
    print("Step 6: Filling delivery address and placing order")
    # Delivery address should be auto-filled; just click "Place Order"
    page.locator("a[href='/payment']").click()
    
    # Step 7: Enter payment details and confirm order
    print("Step 7: Entering payment details")
    page.locator("input[data-qa='name-on-card']").fill("Test User")
    page.locator("input[data-qa='card-number']").fill("4111111111111111")
    page.locator("input[data-qa='cvc']").fill("123")
    page.locator("input[data-qa='expiry-month']").fill("12")
    page.locator("input[data-qa='expiry-year']").fill("2025")
    page.locator("button[data-qa='pay-button']").click()
    
    # Step 8: Verify order success message
    print("Step 8: Verifying order success message")
    expect(page.locator("h2:has-text('Order Placed!')")).to_be_visible()
    expect(page.locator("p:has-text('Congratulations! Your order has been confirmed!')")).to_be_visible()
    
    print("TC_017 completed successfully: Order placed after registering during checkout")