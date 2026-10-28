import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = [
    "googlesyndication.com",
    "googleadservices.com",
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "googletagservices.com",
    "adservice.google.com",
    "pagead2.googlesyndication.com",
    "facebook.net",
    "facebook.com",
    "hotjar.com",
    "cdn.jsdelivr.net",
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
    yield page
    context.close()


def test_verify_subscription_in_cart_page(page: Page):
    print("Starting TC_012: Verify subscription in cart page")

    # Step 1: Navigate to the site and click on 'Cart' button
    print("Step 1: Navigating to automationexercise.com and clicking Cart button")
    _goto_with_retry(page, "https://automationexercise.com")
    cart_link = page.locator("a[href='/view_cart']").first
    expect(cart_link).to_be_visible(timeout=30000)
    cart_link.click()
    expect(page).to_have_url("https://automationexercise.com/view_cart")
    print("Cart page loaded")

    # Step 2: Scroll to the bottom of the cart page
    print("Step 2: Scrolling to the bottom of the cart page")
    page.locator("#footer").scroll_into_view_if_needed()

    # Step 3: Enter email in subscription input
    print("Step 3: Entering email in subscription input")
    subscription_input = page.locator("#susbscribe_email").first
    expect(subscription_input).to_be_visible(timeout=15000)
    subscription_input.fill("cartsubscriber@example.com")

    # Step 4: Click the subscribe arrow button
    print("Step 4: Clicking subscribe arrow button")
    page.locator("#subscribe").first.click()

    # Step 5: Verify success message
    print("Step 5: Verifying success message")
    success_message = page.locator("#success-subscribe").first
    expect(success_message).to_be_visible(timeout=15000)
    expect(success_message).to_contain_text("You have been successfully subscribed!")
    print("Success message verified: 'You have been successfully subscribed!'")

    print("TC_012 completed successfully")