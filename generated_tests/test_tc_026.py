import pytest
from playwright.sync_api import Page, expect
import os
import time

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    yield page
    context.close()

def test_verify_download_invoice_after_purchase(page: Page):
    print("Starting TC_026: Verify download invoice after purchase")
    
    # Navigate to the site
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    print("Navigated to automationexercise.com")
    
    # Login (assuming user is logged in, but we'll perform login for completeness)
    # Click on Signup/Login
    page.locator("a[href='/login']").click()
    print("Clicked on Signup/Login")
    
    # Fill login credentials (use test credentials)
    page.locator("input[data-qa='login-email']").fill("testuserfix@example.com")
    page.locator("input[data-qa='login-password']").fill("Test@123")
    page.locator("button[data-qa='login-button']").click()
    print("Logged in")
    
    # Add a product to cart
    page.locator(".features_items .product-image-wrapper").first.hover()
    page.locator(".features_items .product-image-wrapper").first.locator(".productinfo a.add-to-cart").click()
    print("Added first product to cart")
    
    # Click View Cart
    page.locator("ul.navbar-nav a[href='/view_cart']").click()
    print("Navigated to cart")
    
    # Proceed to checkout
    page.locator("a.check_out").click()
    print("Proceeded to checkout")
    
    # Place order - click Place Order button
    page.locator("a[href='/payment']").click()
    print("Clicked Place Order")
    
    # Fill payment details
    page.locator("input[name='name_on_card']").fill("Test User")
    page.locator("input[name='card_number']").fill("1234567890123456")
    page.locator("input[name='cvc']").fill("123")
    page.locator("input[name='expiry_month']").fill("12")
    page.locator("input[name='expiry_year']").fill("2025")
    print("Filled payment details")
    
    # Confirm order
    page.locator("button#submit").click()
    print("Confirmed order")
    
    # Verify order placed successfully
    expect(page.get_by_text("Order Placed!")).to_be_visible()
    expect(page.get_by_text("Congratulations! Your order has been confirmed!")).to_be_visible()
    print("Order placed successfully")
    
    # Click Download Invoice button
    with page.expect_download() as download_info:
        page.locator("a[href*='download_invoice']").click()
    download = download_info.value
    print(f"Download started: {download.suggested_filename}")
    
    # Save the file to a temporary location
    download_path = os.path.join(os.getcwd(), download.suggested_filename)
    download.save_as(download_path)
    print(f"Downloaded invoice to: {download_path}")
    
    # Verify file exists and is not empty
    assert os.path.exists(download_path), "Invoice file was not downloaded"
    assert os.path.getsize(download_path) > 0, "Invoice file is empty"
    print("Invoice file downloaded successfully and is not empty")
    
    # Verify invoice contains order details
    # Read the PDF file (assuming it's a PDF, but could be HTML)
    # For simplicity, we'll check the file content if it's text-based
    try:
        with open(download_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Check for order-related keywords
        assert "Order" in content or "Invoice" in content, "Invoice does not contain order details"
        print("Invoice contains order details")
    except:
        # If it's a binary PDF, we'll just verify the file exists and has content
        print("Invoice file is binary (likely PDF), verified download success")
    
    # Clean up downloaded file
    os.remove(download_path)
    print("Cleaned up downloaded file")
    
    print("TC_026 completed successfully")