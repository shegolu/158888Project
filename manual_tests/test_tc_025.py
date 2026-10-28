import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_address_details_in_checkout(page: Page):
    print("Starting TC_025: Verify address details in checkout page")
    
    # Precondition: Navigate to the site
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    print("Navigated to automationexercise.com")
    
    # Precondition: Login with valid credentials (assuming user exists)
    page.locator("a[href='/login']").click()
    page.locator("input[data-qa='login-email']").fill("testuserfix@example.com")
    page.locator("input[data-qa='login-password']").fill("Test@123")
    page.locator("button[data-qa='login-button']").click()
    print("Logged in with valid credentials")
    
    # Precondition: Add a product to cart
    page.locator("a[href='/products']").click()
    first_product = page.locator(".features_items .product-image-wrapper").first
    first_product.hover()
    first_product.locator("a.add-to-cart").first.click()
    print("Product added to cart")
    
    # Step 1: Click on 'Cart' button
    page.locator("ul.navbar-nav a[href='/view_cart']").click()
    print("Step 1: Clicked on Cart button")
    
    # Step 2: Click 'Proceed To Checkout' button
    page.locator("a[class*='check_out']").click()
    print("Step 2: Clicked Proceed To Checkout")
    
    # Step 3: Verify delivery and billing address sections are displayed
    delivery_address = page.locator("#address_delivery")
    billing_address = page.locator("#address_invoice")
    expect(delivery_address).to_be_visible()
    expect(billing_address).to_be_visible()
    print("Step 3: Delivery and billing address sections are visible")
    
    # Step 4: Verify address details match user's account details
    # Assuming user's account details are known (e.g., first name, last name, address)
    # We'll verify the address text contains expected values
    expected_name = "Updated User"  # Adjust based on actual user data
    expected_address = "456 New St"  # Adjust based on actual user data
    
    delivery_text = delivery_address.inner_text()
    billing_text = billing_address.inner_text()
    
    assert expected_name in delivery_text, f"Delivery address missing name: {expected_name}"
    assert expected_address in delivery_text, f"Delivery address missing address: {expected_address}"
    assert expected_name in billing_text, f"Billing address missing name: {expected_name}"
    assert expected_address in billing_text, f"Billing address missing address: {expected_address}"
    
    print("Step 4: Address details match user's account details")
    print("TC_025 completed successfully")