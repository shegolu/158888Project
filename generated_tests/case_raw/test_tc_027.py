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
    "adsbygoogle",
    "amazon-adsystem.com",
    "criteo.com",
    "taboola.com",
    "outbrain.com",
)


def _install_routes(page: Page) -> None:
    def _handler(route):
        url = route.request.url
        if any(host in url for host in AD_HOSTS):
            route.abort()
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


def test_verify_scroll_up_down_with_arrow_button(page: Page):
    print("Starting TC_027: Verify scroll up/down functionality with arrow button")

    # Navigate to the site with retry to avoid flaky hangs
    last_error = None
    for attempt in range(3):
        try:
            page.goto(
                "https://automationexercise.com",
                wait_until="commit",
                timeout=30000,
            )
            page.wait_for_selector("header", state="visible", timeout=30000)
            last_error = None
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            page.wait_for_timeout(1000)
    if last_error is not None:
        raise last_error
    print("Step 0: Navigated to https://automationexercise.com")

    # Step 1: Scroll down to the bottom of the page
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    print("Step 1: Scrolled down to the bottom of the page")

    # Step 2: Click the arrow button to scroll up
    arrow_button = page.locator("#scrollUp, .scrollup, a[href='#top']").first
    arrow_button.wait_for(state="visible", timeout=15000)
    arrow_button.click()
    print("Step 2: Clicked the arrow button to scroll up")

    # Step 3: Verify that the page scrolls up to the top
    page.wait_for_function("window.scrollY === 0")
    print("Step 3: Verified page scrolled up to the top")

    # Step 4: Verify that the header is visible
    header = page.locator("header")
    expect(header).to_be_visible()
    print("Step 4: Verified header is visible")

    print("TC_027 completed successfully")