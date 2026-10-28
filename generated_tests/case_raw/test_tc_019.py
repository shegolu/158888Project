import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = [
    "googlesyndication.com",
    "googletagmanager.com",
    "google-analytics.com",
    "doubleclick.net",
    "adservice.google.com",
    "facebook.net",
    "facebook.com",
    "amazon-adsystem.com",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
    "hotjar.com",
    "quantserve.com",
    "scorecardresearch.com",
]


def _install_routes(page: Page) -> None:
    def _handler(route):
        url = route.request.url
        if any(host in url for host in AD_HOSTS):
            route.abort()
            return
        if "automationexercise.com/static/js/" in url:
            route.fulfill(status=200, content_type="application/javascript", body="")
            return
        route.continue_()

    page.route("**/*", _handler)


def _goto_with_retry(page: Page, url: str, attempts: int = 3) -> None:
    last_error = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="commit", timeout=15000)
            page.wait_for_selector(".features_items", state="visible", timeout=20000)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise last_error


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    _install_routes(page)
    yield page
    context.close()


def test_verify_place_order_login_before_checkout(page: Page):
    print("Starting TC_019: Verify place order with login before checkout")

    # Precondition: Navigate to the site
    print("Step 0: Navigating to automationexercise.com")
    _goto_with_retry(page, "https://automationexercise.com")
    expect(page).to_have_title("Automation Exercise")

    # Add a product to cart (assuming first product)
    print("Adding a product to cart")
    first_product = page.locator(".features_items .product-image-wrapper").first
    first_product.hover()
    first_product.locator(".product-overlay a.add-to-cart").first.click()
    continue_btn = page.locator(".modal-footer .btn-success")
    expect(continue_btn).to_be_visible(timeout=15000)
    continue_btn.click()

    # Step 1: Login with valid credentials
    print("Step 1: Logging in with valid credentials")
    page.locator("a[href='/login']").first.click()
    page.locator("input[data-qa='login-email']").fill("testuserfix@example.com")
    page.locator("input[data-qa='login-password']").fill("Test@123")
    page.locator("button[data-qa='login-button']").click()
    expect(page.locator("a[href='/logout']")).to_be_visible()
    print("Login successful")

    # Step 2: Click on 'Cart' button
    print("Step 2: Clicking on Cart button")
    page.locator("a[href='/view_cart']").first.click()
    expect(page.locator("li.active")).to_have_text("Shopping Cart")

    # Step 3: Click 'Proceed To Checkout' button
    print("Step 3: Clicking Proceed To Checkout")
    page.locator("a.btn.btn-default.check_out").first.click()
    expect(page.locator("li.active")).to_have_text("Checkout")

    # Step 4: Fill in delivery address and place order
    print("Step 4: Filling delivery address and placing order")
    expect(page.locator("#address_delivery .address_firstname")).to_contain_text("Updated User")
    page.locator("a.btn.btn-default.check_out").first.click()  # Place Order button

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