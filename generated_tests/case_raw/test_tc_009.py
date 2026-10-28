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


@pytest.fixture
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
            page.wait_for_selector("a[href='/products']", state="visible", timeout=30000)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            try:
                page.wait_for_timeout(1000)
            except Exception:
                pass
    raise last_error


def test_verify_search_product_with_valid_keyword(page):
    print("Starting TC_009: Verify search product with valid keyword")

    # Step 1: Navigate to the site
    print("Step 1: Navigating to automationexercise.com")
    _goto_with_retry(page, "https://automationexercise.com")

    # Step 2: Click on 'Products' button
    print("Step 2: Clicking on 'Products' button")
    page.locator("a[href='/products']").first.click(no_wait_after=True)

    # Step 3: Enter 'T-Shirt' in the search box
    print("Step 3: Entering 'T-Shirt' in the search box")
    search_box = page.locator("#search_product")
    search_box.wait_for(state="visible", timeout=30000)
    search_box.fill("T-Shirt")

    # Step 4: Click 'Search' button
    print("Step 4: Clicking 'Search' button")
    page.locator("#submit_search").click(no_wait_after=True)

    # Step 5: Verify that the search results are displayed
    print("Step 5: Verifying search results are displayed")
    search_results = page.locator(".features_items")
    expect(search_results).to_be_visible()

    # Step 6: Verify that all products contain 'T-Shirt' in their name
    print("Step 6: Verifying all products contain 'T-Shirt' in their name")
    product_names = page.locator(".productinfo p")
    count = product_names.count()
    assert count > 0, "No products found in search results"

    for i in range(count):
        product_name = product_names.nth(i).inner_text()
        assert "T-Shirt" in product_name, f"Product '{product_name}' does not contain 'T-Shirt'"

    print("TC_009 completed successfully: All products contain 'T-Shirt'")