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


def test_verify_subscription_in_home_page(page):
    print("Starting TC_011: Verify subscription in home page")

    # Precondition: Navigate to the site (robust against flaky load)
    print("Step 0: Navigating to automationexercise.com")
    last_error = None
    for _ in range(3):
        try:
            page.goto(
                "https://automationexercise.com",
                wait_until="commit",
                timeout=30000,
            )
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    else:
        raise last_error

    # Wait for a business-critical visible element before proceeding
    page.locator("h2", has_text="Subscription").first.wait_for(
        state="visible", timeout=30000
    )

    # Step 1: Scroll to the bottom of the home page
    print("Step 1: Scrolling to the bottom of the home page")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    # Step 2: Enter email in subscription input
    print("Step 2: Entering email in subscription input")
    email_input = page.locator("#susbscribe_email").first
    email_input.wait_for(state="visible", timeout=30000)
    email_input.fill("subscriber@example.com")

    # Step 3: Click the subscribe arrow button
    print("Step 3: Clicking the subscribe arrow button")
    subscribe_button = page.locator("#subscribe").first
    subscribe_button.click()

    # Step 4: Verify success message
    print("Step 4: Verifying success message")
    success_message = page.locator(".alert-success").first
    expect(success_message).to_be_visible()
    expect(success_message).to_contain_text("You have been successfully subscribed!")

    print("TC_011 completed successfully")