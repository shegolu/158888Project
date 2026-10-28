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
    "scorecardresearch.com",
    "quantserve.com",
    "amazon-adsystem.com",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
]


def _install_routes(page):
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


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    _install_routes(page)
    yield page
    context.close()


def test_view_brand_products(page):
    print("Starting TC_021: Verify view brand products")

    # Step 1: Navigate to the site (robust navigation with retry)
    print("Step 1: Navigating to automationexercise.com")
    last_error = None
    for attempt in range(3):
        try:
            page.goto("https://automationexercise.com", wait_until="commit", timeout=30000)
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"Navigation attempt {attempt + 1} failed: {exc}")
    if last_error is not None:
        raise last_error

    # Wait for business-critical element (brands sidebar heading)
    brands_heading = page.locator("div.brands_products h2")
    brands_heading.wait_for(state="visible", timeout=30000)

    # Step 2: Scroll to the left sidebar (brands section)
    print("Step 2: Scrolling to the left sidebar")
    brands_heading.scroll_into_view_if_needed()
    expect(brands_heading).to_be_visible()
    print("Left sidebar with brands is visible")

    # Step 3: Click on the 'Polo' brand
    print("Step 3: Clicking on the 'Polo' brand")
    polo_link = page.locator("div.brands_products a", has_text="Polo").first
    polo_link.click()

    # Step 4: Verify that brand products are displayed
    print("Step 4: Verifying brand products are displayed")

    # Wait for the brand products page to load before asserting URL
    brand_title = page.locator("h2.title.text-center")
    brand_title.wait_for(state="visible", timeout=30000)

    expect(page).to_have_url("https://automationexercise.com/brand_products/Polo", timeout=15000)

    expect(brand_title).to_contain_text("Brand - Polo")

    products = page.locator("div.productinfo")
    products.first.wait_for(state="visible", timeout=30000)
    expect(products.first).to_be_visible()

    product_count = products.count()
    print(f"Number of Polo products displayed: {product_count}")
    assert product_count > 0, "No products found for the Polo brand"

    print("TC_021 completed successfully: Brand products are displayed")