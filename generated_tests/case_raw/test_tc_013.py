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
    "twitter.com",
    "analytics",
    "adsbygoogle",
]


def _setup_routes(page: Page) -> None:
    def _handle(route):
        url = route.request.url
        if any(host in url for host in AD_HOSTS):
            route.abort()
            return
        if "automationexercise.com/static/js/" in url:
            route.fulfill(status=200, content_type="application/javascript", body="")
            return
        route.continue_()

    page.route("**/*", _handle)


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


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    _setup_routes(page)
    yield page
    context.close()


def test_verify_add_single_product_to_cart(page: Page):
    print("Starting TC_013: Verify add single product to cart")

    # Step 1: Navigate to the site and click on 'Products' button
    print("Step 1: Navigating to automationexercise.com and clicking Products button")
    _goto_with_retry(page, "https://automationexercise.com")
    products_link = page.locator("a[href='/products']").first
    expect(products_link).to_be_visible(timeout=30000)
    products_link.click()
    expect(page).to_have_url("https://automationexercise.com/products")
    expect(page.locator(".features_items .product-image-wrapper").first).to_be_visible(timeout=30000)
    print("Products page loaded")

    # Step 2: Hover over the first product and click 'Add to cart'
    print("Step 2: Hovering over first product and clicking Add to cart")
    first_product = page.locator(".features_items .product-image-wrapper").first
    add_to_cart_btn = first_product.locator(".productinfo .add-to-cart").first
    expect(add_to_cart_btn).to_be_visible(timeout=30000)
    add_to_cart_btn.click()
    print("Add to cart clicked")

    # Step 3: Click 'View Cart' button (from the confirmation modal)
    print("Step 3: Clicking View Cart button")
    cart_modal = page.locator("#cartModal")
    expect(cart_modal).to_be_visible(timeout=30000)
    view_cart_link = cart_modal.locator("a[href='/view_cart']").first
    expect(view_cart_link).to_be_visible(timeout=30000)
    view_cart_link.click()
    expect(page).to_have_url("https://automationexercise.com/view_cart")
    print("Cart page loaded")

    # Step 4: Verify that the product is in the cart
    print("Step 4: Verifying product is in cart")
    cart_items = page.locator("#cart_info_table tbody tr")
    expect(cart_items).to_have_count(1)
    expect(cart_items.first).to_contain_text("Blue Top")
    print("Product verified in cart")

    print("TC_013 completed successfully")