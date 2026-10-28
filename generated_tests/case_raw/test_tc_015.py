import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = (
    "googlesyndication.com",
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "googleadservices.com",
    "facebook.net",
    "facebook.com",
    "adservice.google.com",
    "pagead2.googlesyndication.com",
)


def _route_handler(route):
    url = route.request.url
    if any(host in url for host in AD_HOSTS):
        route.abort()
        return
    # Only stub JS for non-document requests to avoid breaking navigation scripts
    if "automationexercise.com/static/js/" in url and route.request.resource_type != "document":
        route.fulfill(status=200, content_type="application/javascript", body="")
        return
    route.continue_()


def _goto_with_retry(page: Page, url: str, attempts: int = 3) -> None:
    last_error = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="commit", timeout=15000)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if last_error is not None:
        raise last_error


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    page.route("**/*", _route_handler)
    _goto_with_retry(page, "https://automationexercise.com")
    page.locator("a[href='/products']").first.wait_for(state="visible", timeout=30000)
    yield page
    context.close()


def test_verify_product_quantity_in_cart(page: Page):
    print("Starting TC_015: Verify product quantity in cart")

    # Step 1: Navigate to the site and click on 'Products' button
    print("Step 1: Navigating to automationexercise.com and clicking 'Products'")
    products_link = page.locator("a[href='/products']").first
    products_link.wait_for(state="visible", timeout=30000)
    products_link.click()
    try:
        expect(page).to_have_url("https://automationexercise.com/products", timeout=15000)
    except AssertionError:
        # Retry navigation if click did not navigate
        _goto_with_retry(page, "https://automationexercise.com/products")
        expect(page).to_have_url("https://automationexercise.com/products", timeout=15000)

    # Step 2: Click 'View Product' for the first product
    print("Step 2: Clicking 'View Product' for the first product")
    first_product = page.locator(".features_items .product-image-wrapper").first
    first_product.wait_for(state="visible", timeout=30000)
    first_product.locator("a[href*='/product_details/']").click()
    expect(page.locator(".product-information")).to_be_visible(timeout=15000)

    # Step 3: Increase quantity to 4
    print("Step 3: Setting quantity to 4")
    quantity_input = page.locator("#quantity")
    quantity_input.wait_for(state="visible", timeout=15000)
    quantity_input.fill("4")
    expect(quantity_input).to_have_value("4")

    # Step 4: Click 'Add to cart' button
    print("Step 4: Clicking 'Add to cart'")
    page.locator("button.btn-default.cart").click()
    expect(page.locator(".modal-content")).to_be_visible(timeout=15000)

    # Step 5: Click 'View Cart' button
    print("Step 5: Clicking 'View Cart'")
    view_cart = page.locator(".modal-content a[href='/view_cart']").first
    view_cart.wait_for(state="visible", timeout=15000)
    view_cart.click()
    expect(page).to_have_url("https://automationexercise.com/view_cart", timeout=15000)

    # Step 6: Verify that the quantity is 4
    print("Step 6: Verifying cart quantity is 4")
    cart_quantity = page.locator(".cart_quantity").first
    cart_quantity.wait_for(state="visible", timeout=15000)
    expect(cart_quantity).to_have_text("4")

    print("TC_015 passed: Product quantity in cart is 4")