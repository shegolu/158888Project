import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = [
    "googlesyndication.com",
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "googletagservices.com",
    "facebook.net",
    "facebook.com",
    "adservice.google.com",
    "amazon-adsystem.com",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
    "scorecardresearch.com",
    "quantserve.com",
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
            page.goto(url, wait_until="commit", timeout=30000)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if last_error is not None:
        raise last_error


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    _install_routes(page)
    _goto_with_retry(page, "https://automationexercise.com")
    expect(page.locator("a[href='/'] img[alt='Website for automation practice']").first).to_be_visible(timeout=30000)
    yield page
    context.close()


def test_verify_add_to_cart_from_recommended_items(page):
    print("Starting TC_024: Verify add to cart from recommended items")

    # Step 1: Navigate to the home page (already done in fixture)
    print("Step 1: Home page loaded")

    # Step 2: Scroll to the bottom of the home page
    print("Step 2: Scrolling to the bottom of the home page")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    # Step 3: Verify that 'RECOMMENDED ITEMS' are visible
    print("Step 3: Verifying 'RECOMMENDED ITEMS' section is visible")
    recommended_items_header = page.locator("h2:has-text('recommended items')")
    expect(recommended_items_header).to_be_visible()
    print("'RECOMMENDED ITEMS' section is visible")

    # Step 4: Click 'Add to cart' on a recommended product
    print("Step 4: Clicking 'Add to cart' on a recommended product")
    add_to_cart_button = page.locator("#recommended-item-carousel .item.active .add-to-cart").first
    expect(add_to_cart_button).to_be_visible()
    add_to_cart_button.click()
    print("Clicked 'Add to cart' on the first recommended product")

    # Wait for the cart modal to appear
    cart_modal = page.locator("#cartModal")
    expect(cart_modal).to_be_visible(timeout=10000)

    # Step 5: Click 'View Cart' button inside the modal
    print("Step 5: Clicking 'View Cart' button")
    view_cart_button = cart_modal.locator("a:has-text('View Cart')")
    expect(view_cart_button).to_be_visible()
    view_cart_button.click()
    print("Clicked 'View Cart' button")

    # Step 6: Verify that the product is in the cart
    print("Step 6: Verifying the product is in the cart")
    cart_page = page.locator("#cart_items")
    expect(cart_page).to_be_visible()

    cart_products = page.locator("#cart_info_table tbody tr")
    expect(cart_products.first).to_be_visible()
    print("Product is successfully added to the cart")

    print("TC_024 completed successfully")