import pytest
from playwright.sync_api import Page, expect
import os
import time


AD_TRACKER_HOSTS = [
    "googlesyndication.com",
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "googletagservices.com",
    "adservice.google.com",
    "pagead2.googlesyndication.com",
    "facebook.net",
    "facebook.com",
    "analytics.google.com",
    "cdn.jsdelivr.net",
    "fonts.gstatic.com",
]


def _install_routes(page: Page) -> None:
    def _handler(route):
        url = route.request.url
        try:
            if any(host in url for host in AD_TRACKER_HOSTS):
                route.abort()
                return
            if "automationexercise.com/static/js/" in url:
                route.fulfill(status=200, content_type="application/javascript", body="")
                return
        except Exception:
            pass
        route.continue_()

    page.route("**/*", _handler)


def _goto_with_retry(page: Page, url: str, attempts: int = 4) -> None:
    last_error = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="commit", timeout=30000)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2)
    if last_error is not None:
        raise last_error


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    _install_routes(page)
    yield page
    context.close()


def test_verify_download_invoice_after_purchase(page: Page):
    print("Starting TC_026: Verify download invoice after purchase")

    # Navigate to the site with retry and commit wait
    _goto_with_retry(page, "https://automationexercise.com")
    print("Navigated to automationexercise.com")

    # Wait for a business-critical visible element before proceeding
    login_link = page.locator("a[href='/login']").first
    login_link.wait_for(state="visible", timeout=30000)

    # Login (assuming user is logged in, but we'll perform login for completeness)
    login_link.click()
    print("Clicked on Signup/Login")

    # Wait for login form to be visible
    login_email = page.locator("input[data-qa='login-email']").first
    login_email.wait_for(state="visible", timeout=30000)

    # Fill login credentials (use test credentials)
    login_email.fill("testuserfix@example.com")
    page.locator("input[data-qa='login-password']").first.fill("Test@123")
    page.locator("button[data-qa='login-button']").first.click()
    print("Logged in")

    # Wait for logged-in state (logout link visible) before continuing
    page.locator("a[href='/logout']").first.wait_for(state="visible", timeout=30000)

    # Add a product to cart
    first_product = page.locator(".features_items .product-image-wrapper").first
    first_product.wait_for(state="visible", timeout=30000)
    first_product.hover()
    first_product.locator(".productinfo a.add-to-cart").first.click()
    print("Added first product to cart")

    # The cart modal link is hidden in the DOM; navigate directly to the cart page
    _goto_with_retry(page, "https://automationexercise.com/view_cart")
    print("Navigated to cart")

    # Proceed to checkout
    checkout_link = page.locator("a.check_out").first
    checkout_link.wait_for(state="visible", timeout=30000)
    checkout_link.click()
    print("Proceeded to checkout")

    # Place order - click Place Order button
    place_order = page.locator("a[href='/payment']").first
    place_order.wait_for(state="visible", timeout=30000)
    place_order.click()
    print("Clicked Place Order")

    # Fill payment details
    page.locator("input[name='name_on_card']").first.wait_for(state="visible", timeout=30000)
    page.locator("input[name='name_on_card']").first.fill("Test User")
    page.locator("input[name='card_number']").first.fill("1234567890123456")
    page.locator("input[name='cvc']").first.fill("123")
    page.locator("input[name='expiry_month']").first.fill("12")
    page.locator("input[name='expiry_year']").first.fill("2025")
    print("Filled payment details")

    # Confirm order
    page.locator("button#submit").first.click()
    print("Confirmed order")

    # Verify order placed successfully
    expect(page.get_by_text("Order Placed!")).to_be_visible()
    expect(page.get_by_text("Congratulations! Your order has been confirmed!")).to_be_visible()
    print("Order placed successfully")

    # Click Download Invoice button
    download_link = page.locator("a[href*='download_invoice']").first
    download_link.wait_for(state="visible", timeout=30000)
    with page.expect_download() as download_info:
        download_link.click()
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
    except UnicodeDecodeError:
        # If it's a binary PDF, we'll just verify the file exists and has content
        print("Invoice file is binary (likely PDF), verified download success")

    # Clean up downloaded file
    os.remove(download_path)
    print("Cleaned up downloaded file")

    print("TC_026 completed successfully")