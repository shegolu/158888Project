import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = [
    "googlesyndication.com",
    "googletagmanager.com",
    "google-analytics.com",
    "doubleclick.net",
    "googleadservices.com",
    "facebook.net",
    "facebook.com",
    "adservice.google.com",
    "amazon-adsystem.com",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
    "pagead2.googlesyndication.com",
]

# Third-party JS that is safe to stub out (does not affect site functionality).
STUB_JS_HOSTS = [
    "googlesyndication.com",
    "googletagmanager.com",
    "google-analytics.com",
    "doubleclick.net",
    "googleadservices.com",
    "facebook.net",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
]


def _install_routes(page: Page):
    def handler(route):
        url = route.request.url
        if any(host in url for host in AD_HOSTS):
            route.abort()
            return
        # Only stub third-party JS, never the site's own scripts.
        if any(host in url for host in STUB_JS_HOSTS) and url.endswith(".js"):
            route.fulfill(status=200, content_type="application/javascript", body="")
            return
        route.continue_()

    page.route("**/*", handler)


def _goto_home(page: Page):
    last_err = None
    for _ in range(3):
        try:
            page.goto("https://automationexercise.com", wait_until="commit", timeout=20000)
            # Wait for a business-critical element that does not depend on JS.
            page.locator('header#header a[href="/"]').first.wait_for(
                state="visible", timeout=20000
            )
            return
        except Exception as e:
            last_err = e
            try:
                page.goto(
                    "https://automationexercise.com",
                    wait_until="domcontentloaded",
                    timeout=20000,
                )
                page.locator('header#header a[href="/"]').first.wait_for(
                    state="visible", timeout=20000
                )
                return
            except Exception as e2:
                last_err = e2
    raise last_err


@pytest.fixture(scope="function")
def browser_context(page: Page):
    _install_routes(page)
    _goto_home(page)
    yield page


def test_verify_search_products_and_cart_after_login(browser_context: Page):
    page = browser_context
    print("Starting TC_022: Verify search products and verify cart after login")

    # Step 1: Search for a product and add it to cart
    print("Step 1: Searching for a product and adding to cart")
    search_input = page.locator('input[name="search"]').first
    search_input.wait_for(state="visible", timeout=30000)
    search_input.fill("dress")
    page.locator('#search_product').first.click()
    first_product_add_to_cart = page.locator('.productinfo .btn-add-to-cart').first
    first_product_add_to_cart.wait_for(state="visible", timeout=30000)
    first_product_add_to_cart.click()
    continue_btn = page.locator('.modal-footer .btn-success').first
    continue_btn.wait_for(state="visible", timeout=30000)
    continue_btn.click()

    # Step 2: Click 'Cart' and verify the product is in the cart
    print("Step 2: Clicking Cart and verifying product")
    page.locator('a[href="/view_cart"]').first.click()
    cart_items = page.locator('.cart_info tbody tr')
    expect(cart_items).to_have_count(1)
    expect(page.locator('.cart_description a').first).to_contain_text("dress")
    print("Product verified in cart before login")

    # Step 3: Logout
    print("Step 3: Logging out")
    page.locator('a[href="/logout"]').first.click()
    expect(page.locator('a[href="/login"]').first).to_be_visible()

    # Step 4: Login with valid credentials
    print("Step 4: Logging in with valid credentials")
    page.locator('a[href="/login"]').first.click()
    page.locator('input[data-qa="login-email"]').fill("testuser@example.com")
    page.locator('input[data-qa="login-password"]').fill("password123")
    page.locator('button[data-qa="login-button"]').click()
    expect(page.locator('a[href="/logout"]').first).to_be_visible()

    # Step 5: Click 'Cart' and verify the product is still in the cart
    print("Step 5: Clicking Cart after login and verifying product")
    page.locator('a[href="/view_cart"]').first.click()
    cart_items_after_login = page.locator('.cart_info tbody tr')
    expect(cart_items_after_login).to_have_count(1)
    expect(page.locator('.cart_description a').first).to_contain_text("dress")
    print("Product verified in cart after login")

    print("TC_022 completed successfully")