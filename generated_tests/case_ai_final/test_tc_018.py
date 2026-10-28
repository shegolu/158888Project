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
    "quantserve.com",
    "scorecardresearch.com",
    "hotjar.com",
    "zendesk.com",
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
    last_err = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="commit", timeout=30000)
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    if last_err is not None:
        raise last_err


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    _install_routes(page)
    yield page
    context.close()


def test_verify_place_order_register_before_checkout(page: Page):
    print("TC_018: Verify place order - register before checkout")

    # Step 0: Navigate to the site
    print("Step 0: Navigating to automationexercise.com")
    _goto_with_retry(page, "https://automationexercise.com")
    expect(page).to_have_title("Automation Exercise")

    # Precondition: Add a product to cart
    print("Precondition: Adding a product to cart")
    add_to_cart = page.locator(".features_items .productinfo a[data-product-id='1']").first
    expect(add_to_cart).to_be_visible()
    add_to_cart.click()

    # Wait for the modal to appear and click Continue Shopping
    continue_btn = page.locator("#cartModal button.close-modal")
    expect(continue_btn).to_be_visible()
    continue_btn.click()
    expect(continue_btn).to_be_hidden()

    # Step 1: Register a new account before checkout
    print("Step 1: Registering a new account")
    page.locator("a[href='/login']").click()
    expect(page).to_have_url("https://automationexercise.com/login")

    # Signup
    import random
    email = f"testuserproject{random.randint(1000,9999)}@example.com"
    page.locator("input[data-qa='signup-name']").fill("Test User")
    page.locator("input[data-qa='signup-email']").fill(email)
    page.locator("button[data-qa='signup-button']").click()

    # Fill account information
    page.locator("#id_gender1").check()
    page.locator("input[data-qa='password']").fill("password123")
    page.locator("select[data-qa='days']").select_option("10")
    page.locator("select[data-qa='months']").select_option("5")
    page.locator("select[data-qa='years']").select_option("1990")
    page.locator("input[data-qa='first_name']").fill("Test")
    page.locator("input[data-qa='last_name']").fill("User")
    page.locator("input[data-qa='company']").fill("TestCompany")
    page.locator("input[data-qa='address']").fill("123 Test Street")
    page.locator("input[data-qa='address2']").fill("Apt 4")
    page.locator("select[data-qa='country']").select_option("United States")
    page.locator("input[data-qa='state']").fill("California")
    page.locator("input[data-qa='city']").fill("Los Angeles")
    page.locator("input[data-qa='zipcode']").fill("90001")
    page.locator("input[data-qa='mobile_number']").fill("1234567890")
    page.locator("button[data-qa='create-account']").click()

    expect(page.locator("h2[data-qa='account-created']")).to_be_visible()
    page.locator("a[data-qa='continue-button']").click()

    # Step 2: Click on 'Cart' button
    print("Step 2: Clicking on Cart button")
    page.locator("a[href='/view_cart']").first.click()
    expect(page).to_have_url("https://automationexercise.com/view_cart")

    # Step 3: Click 'Proceed To Checkout' button
    print("Step 3: Clicking Proceed To Checkout")
    page.locator("a.check_out").click()
    expect(page).to_have_url("https://automationexercise.com/checkout")

    # Step 4: Fill in delivery address and place order
    print("Step 4: Verifying delivery address and placing order")
    # Verify delivery address is displayed
    expect(page.locator("#address_delivery")).to_contain_text("Test User")
    expect(page.locator("#address_delivery")).to_contain_text("123 Test Street")

    # Place order
    page.locator("a[href='/payment']").click()
    expect(page).to_have_url("https://automationexercise.com/payment")

    # Step 5: Enter payment details and confirm order
    print("Step 5: Entering payment details")
    page.locator("input[data-qa='name-on-card']").fill("Test User")
    page.locator("input[data-qa='card-number']").fill("1234567890123456")
    page.locator("input[data-qa='cvc']").fill("123")
    page.locator("input[data-qa='expiry-month']").fill("12")
    page.locator("input[data-qa='expiry-year']").fill("2025")
    page.locator("button[data-qa='pay-button']").click()

    # Step 6: Verify order success message
    print("Step 6: Verifying order success message")
    expect(page.get_by_role("heading", name="Order Placed!")).to_be_visible()
    expect(page.get_by_text("Congratulations! Your order has been confirmed!")).to_be_visible()
    print("TC_018: Test passed - Order placed successfully after registering before checkout")