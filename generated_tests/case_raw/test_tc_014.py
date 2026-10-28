import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = [
    "googlesyndication.com",
    "googletagmanager.com",
    "google-analytics.com",
    "doubleclick.net",
    "facebook.net",
    "facebook.com",
    "adservice.google.com",
    "fundingchoicesmessages.google.com",
]


def _install_routes(page: Page):
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
def browser_context(page: Page):
    """Setup browser context and navigate to the base URL."""
    print("Setting up browser and navigating to automationexercise.com")
    _install_routes(page)

    last_error = None
    for _ in range(3):
        try:
            page.goto("https://automationexercise.com", wait_until="commit", timeout=30000)
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            page.wait_for_timeout(2000)
    else:
        raise last_error

    # Wait for a business-critical visible element before yielding
    expect(page.locator("a[href='/products']").first).to_be_visible(timeout=30000)
    yield page
    print("Tearing down browser")


def test_add_multiple_products_to_cart(browser_context: Page):
    """TC_014: Verify add multiple products to cart."""
    page = browser_context
    print("Step 1: Click on 'Products' button")
    page.locator("a[href='/products']").first.click()
    expect(page.locator("h2.title.text-center")).to_have_text("All Products", timeout=15000)
    expect(page).to_have_url("https://automationexercise.com/products", timeout=15000)
    print("Products page loaded")

    add_buttons = page.locator(".productinfo.text-center a.btn.btn-default.add-to-cart")
    expect(add_buttons.first).to_be_visible(timeout=30000)

    print("Step 2: Add the first product to cart")
    add_buttons.first.click()
    modal = page.locator("#cartModal")
    expect(modal).to_be_visible(timeout=15000)
    print("First product added to cart")

    print("Step 3: Continue shopping and add the second product to cart")
    continue_btn = modal.locator("button.close-modal")
    expect(continue_btn).to_be_visible(timeout=15000)
    continue_btn.click()
    expect(modal).to_be_hidden(timeout=15000)

    second_product_add = add_buttons.nth(1)
    expect(second_product_add).to_be_visible(timeout=15000)
    second_product_add.click()
    expect(modal).to_be_visible(timeout=15000)
    print("Second product added to cart")

    print("Step 4: Click 'View Cart' button")
    page.locator("a[href='/view_cart']").first.click()
    expect(page).to_have_url("https://automationexercise.com/view_cart", timeout=15000)
    print("Cart page loaded")

    print("Step 5: Verify that both products are in the cart")
    cart_items = page.locator("tr.cart_item")
    expect(cart_items).to_have_count(2)
    expect(page.locator("td.cart_description h4 a")).to_have_count(2)
    print("Both products verified in cart")

    print("Test TC_014 passed")