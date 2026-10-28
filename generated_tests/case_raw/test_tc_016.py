import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = [
    "googlesyndication.com",
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "googletagservices.com",
    "adservice.google.com",
    "facebook.net",
    "facebook.com",
    "amazon-adsystem.com",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
    "scorecardresearch.com",
    "quantserve.com",
    "hotjar.com",
    "youtube.com",
    "ytimg.com",
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


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    _install_routes(page)
    yield page
    context.close()


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


def test_remove_product_from_cart(page: Page):
    print("Starting TC_016: Verify remove product from cart")

    # Navigate to the site with retry and lightweight wait
    _goto_with_retry(page, "https://automationexercise.com")
    print("Navigated to automationexercise.com")

    # Wait for a business-critical element before proceeding
    add_to_cart = page.locator(
        ".productinfo.text-center a.add-to-cart[data-product-id]"
    ).first
    add_to_cart.wait_for(state="visible", timeout=30000)

    # Add a product to the cart (precondition)
    add_to_cart.click()
    print("Clicked 'Add to cart' on first product")

    # Wait for the confirmation modal, then click "Continue Shopping"
    continue_btn = page.locator("#cartModal button.close-modal").first
    continue_btn.wait_for(state="visible", timeout=15000)
    continue_btn.click()
    print("Clicked 'Continue Shopping'")

    # Step 1: Click on 'Cart' button
    page.locator("li a[href='/view_cart']").first.click()
    print("Step 1: Clicked on 'Cart' button")

    # Verify product is in cart before removal
    expect(page.locator("#cart_info_table")).to_be_visible()
    expect(page.locator("#cart_info_table tbody tr")).to_have_count(1)
    print("Product is present in cart")

    # Step 2: Click the 'X' button to remove the product
    page.locator(".cart_quantity_delete").first.click()
    print("Step 2: Clicked the 'X' button to remove the product")

    # Step 3: Verify that the cart is empty
    expect(page.locator("text=Cart is empty!")).to_be_visible()
    print("Step 3: Verified cart is empty")

    print("TC_016 completed successfully")