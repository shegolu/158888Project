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
    "amazon-adsystem.com",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
)


def _install_routes(page):
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


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    _install_routes(page)
    yield page
    context.close()


def test_verify_search_product_with_invalid_keyword(page):
    print("Starting TC_010: Verify search product with invalid keyword")

    # Step 1: Navigate to the site (robust retry loop)
    print("Step 1: Navigating to automationexercise.com")
    last_error = None
    for _ in range(4):
        try:
            page.goto("https://automationexercise.com", wait_until="commit", timeout=30000)
            expect(page.locator("a[href='/products']").first).to_be_visible(timeout=30000)
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            try:
                page.wait_for_timeout(1000)
            except Exception:  # noqa: BLE001
                pass
    if last_error is not None:
        raise last_error

    # Step 2: Click on 'Products' button
    print("Step 2: Clicking on 'Products' button")
    page.locator("a[href='/products']").first.click()

    # Step 3: Enter invalid keyword in search box
    print("Step 3: Entering 'NonExistentProduct' in search box")
    search_box = page.locator("#search_product")
    search_box.wait_for(state="visible", timeout=30000)
    search_box.fill("NonExistentProduct")

    # Step 4: Click 'Search' button
    print("Step 4: Clicking 'Search' button")
    page.locator("#submit_search").click()

    # Step 5: Verify no products found message
    print("Step 5: Verifying 'No products found' message is displayed")
    no_products_message = page.locator("text=No products found")
    expect(no_products_message).to_be_visible()

    print("TC_010 passed: 'No products found' message is displayed")