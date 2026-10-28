import pytest
from playwright.sync_api import Page, expect

AD_HOSTS = (
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
)

LOGIN_EMAIL = "testuser_tc005@example.com"
LOGIN_PASSWORD = "Password123"


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


def _goto_with_retry(page: Page, url: str) -> None:
    last_error = None
    for _ in range(3):
        try:
            page.goto(url, wait_until="commit", timeout=30000)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise last_error


def _ensure_logged_in(page: Page) -> None:
    # If already logged in (Logout link present), nothing to do.
    if page.locator("a[href='/logout']").count() > 0:
        return

    _goto_with_retry(page, "https://automationexercise.com/login")
    expect(page.locator("h2", has_text="Login to your account").first).to_be_visible(timeout=30000)

    email_input = page.locator("input[data-qa='login-email']").first
    password_input = page.locator("input[data-qa='login-password']").first
    expect(email_input).to_be_visible()
    email_input.fill(LOGIN_EMAIL)
    password_input.fill(LOGIN_PASSWORD)

    page.locator("button[data-qa='login-button']").first.click()

    # Wait for the Logout link to confirm successful login.
    expect(page.locator("a[href='/logout']").first).to_be_visible(timeout=30000)


@pytest.fixture(scope="function")
def browser_context(page: Page):
    _install_routes(page)

    _goto_with_retry(page, "https://automationexercise.com")

    # Wait for a business-critical visible element before yielding
    expect(page.locator("header#header").first).to_be_visible(timeout=30000)

    # Precondition: user is logged in
    _ensure_logged_in(page)

    yield page


def test_verify_user_logout_functionality(browser_context: Page):
    page = browser_context
    print("Starting TC_005: Verify user logout functionality")

    # Step 1: Click on 'Logout' button
    print("Step 1: Clicking on 'Logout' button")
    logout_button = page.locator("a[href='/logout']").first
    expect(logout_button).to_be_visible()
    logout_button.click()

    # Step 2: Verify that the user is navigated to the login page
    print("Step 2: Verifying navigation to login page")
    expect(page).to_have_url("https://automationexercise.com/login")

    # Step 3: Verify that 'Login to your account' is visible
    print("Step 3: Verifying 'Login to your account' is visible")
    login_header = page.locator("h2", has_text="Login to your account").first
    expect(login_header).to_be_visible()

    print("TC_005 completed successfully: User is logged out and redirected to login page")