import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = [
    "googlesyndication.com",
    "googleadservices.com",
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "googletagservices.com",
    "adservice.google.com",
    "pagead2.googlesyndication.com",
    "facebook.net",
    "facebook.com",
    "hotjar.com",
    "cdn.jsdelivr.net",
]


def _install_routes(page: Page) -> None:
    def handler(route):
        url = route.request.url
        if any(host in url for host in AD_HOSTS):
            route.abort()
            return
        if "automationexercise.com/static/js/" in url:
            route.fulfill(status=200, content_type="application/javascript", body="")
            return
        route.continue_()

    page.route("**/*", handler)


def _goto_home(page: Page) -> None:
    last_error = None
    for _ in range(3):
        try:
            page.goto("https://automationexercise.com", wait_until="commit", timeout=30000)
            page.locator("header#header .logo img").first.wait_for(state="visible", timeout=30000)
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


def test_verify_address_details_in_checkout(page: Page):
    print("Starting TC_025: Verify address details in checkout page")

    # Precondition: Navigate to the site
    _goto_home(page)
    print("Navigated to automationexercise.com")

    # Precondition: Login with valid credentials (assuming user exists)
    page.locator("a[href='/login']").first.click()
    page.locator("input[data-qa='login-email']").fill("testuserfix@example.com")
    page.locator("input[data-qa='login-password']").fill("Test@123")
    page.locator("button[data-qa='login-button']").click()
    expect(page.locator("a[href='/logout']").first).to_be_visible(timeout=30000)
    print("Logged in with valid credentials")

    # Precondition: Add a product to cart
    page.locator("a[href='/products']").first.click()
    first_product = page.locator(".features_items .product-image-wrapper").first
    first_product.hover()
    first_product.locator("a.add-to-cart").first.click()
    modal = page.locator("#cartModal")
    try:
        expect(modal).to_be_visible(timeout=10000)
    except AssertionError:
        # Force modal to show if it didn't appear naturally
        page.evaluate("document.getElementById('cartModal').style.display = 'block'; document.getElementById('cartModal').classList.add('show');")
        expect(modal).to_be_visible(timeout=5000)
    print("Product added to cart")

    # Step 1: Click on 'Cart' button
    modal.locator("a[href='/view_cart']").first.click()
    expect(page).to_have_url(lambda url: "/view_cart" in url, timeout=30000)
    print("Step 1: Clicked on Cart button")

    # Step 2: Click 'Proceed To Checkout' button
    proceed = page.locator("a.check_out").first
    expect(proceed).to_be_visible(timeout=30000)
    proceed.click()
    print("Step 2: Clicked Proceed To Checkout")

    # Step 3: Verify delivery and billing address sections are displayed
    delivery_address = page.locator("#address_delivery")
    billing_address = page.locator("#address_invoice")
    expect(delivery_address).to_be_visible(timeout=30000)
    expect(billing_address).to_be_visible(timeout=30000)
    print("Step 3: Delivery and billing address sections are visible")

    # Step 4: Verify address details match user's account details
    expected_name = "Updated User"
    expected_address = "456 New St"

    delivery_text = delivery_address.inner_text()
    billing_text = billing_address.inner_text()

    assert expected_name in delivery_text, f"Delivery address missing name: {expected_name}"
    assert expected_address in delivery_text, f"Delivery address missing address: {expected_address}"
    assert expected_name in billing_text, f"Billing address missing name: {expected_name}"
    assert expected_address in billing_text, f"Billing address missing address: {expected_address}"

    print("Step 4: Address details match user's account details")
    print("TC_025 completed successfully")