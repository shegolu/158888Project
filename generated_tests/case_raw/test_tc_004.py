import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = [
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
]


def _route_handler(route):
    url = route.request.url
    if any(host in url for host in AD_HOSTS):
        route.abort()
        return
    if "automationexercise.com/static/js/" in url:
        route.fulfill(status=200, content_type="application/javascript", body="")
        return
    route.continue_()


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    page.route("**/*", _route_handler)
    yield page
    context.close()


def _goto_with_retry(page, url, attempts=5, timeout=15000):
    last_error = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="commit", timeout=timeout)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            try:
                page.wait_for_timeout(1000)
            except Exception:  # noqa: BLE001
                pass
    if last_error is not None:
        raise last_error


def test_incorrect_login(page):
    print("Starting TC_004: Verify user login with incorrect credentials")

    # Step 1: Navigate to the site and click on 'Signup / Login'
    print("Step 1: Navigating to automationexercise.com and clicking 'Signup / Login'")
    _goto_with_retry(page, "https://automationexercise.com")
    login_link = page.locator("a[href='/login']").first
    expect(login_link).to_be_visible(timeout=30000)
    login_link.click()

    # Step 2: Enter incorrect email and password
    print("Step 2: Entering incorrect email and password")
    email_input = page.locator("input[data-qa='login-email']").first
    expect(email_input).to_be_visible(timeout=30000)
    email_input.fill("wronguser@example.com")
    page.locator("input[data-qa='login-password']").first.fill("WrongPass123")

    # Step 3: Click 'Login' button
    print("Step 3: Clicking 'Login' button")
    page.locator("button[data-qa='login-button']").first.click()

    # Step 4: Verify error message is displayed
    print("Step 4: Verifying error message")
    error_message = page.locator("p[style*='color: red']").first
    expect(error_message).to_be_visible(timeout=30000)
    expect(error_message).to_contain_text("Your email or password is incorrect!")

    print("TC_004 passed: Error message displayed correctly")
