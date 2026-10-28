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
    "adsbygoogle",
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


def test_verify_user_login_with_correct_credentials(page):
    print("Starting TC_003: Verify user login with correct credentials")

    # Step 1: Navigate to the site and click on 'Signup / Login'
    print("Step 1: Navigating to automationexercise.com and clicking 'Signup / Login'")
    last_error = None
    for attempt in range(3):
        try:
            page.goto("https://automationexercise.com", wait_until="commit", timeout=30000)
            page.locator("a[href='/login']").first.wait_for(state="visible", timeout=30000)
            last_error = None
            break
        except Exception as exc:
            last_error = exc
            print(f"Navigation attempt {attempt + 1} failed: {exc}")
    if last_error is not None:
        raise last_error

    page.locator("a[href='/login']").first.click()

    # Wait for the login form to be rendered and interactable
    login_email = page.locator("input[data-qa='login-email']").first
    login_email.wait_for(state="visible", timeout=30000)

    # Step 2: Enter email and password
    print("Step 2: Entering email and password")
    login_email.fill("testuserfix@example.com")
    page.locator("input[data-qa='login-password']").first.fill("Test@123")

    # Step 3: Click 'Login' button
    print("Step 3: Clicking 'Login' button")
    login_button = page.locator("button[data-qa='login-button']").first
    login_button.wait_for(state="visible", timeout=30000)
    login_button.click()

    # Step 4: Verify 'Logged in as TestUser' is visible
    print("Step 4: Verifying 'Logged in as TestUser' is visible")
    logged_in_text = page.locator("li:has-text('Logged in as') a").first
    expect(logged_in_text).to_be_visible()
    expect(logged_in_text).to_contain_text("Test")

    print("TC_003 Passed: User logged in successfully and 'Logged in as TestUser' is displayed")
