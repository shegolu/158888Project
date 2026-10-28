import os
import pytest
from playwright.sync_api import Page, expect

print("Current dir:", os.getcwd())
print("File exists?", os.path.exists("test_file.txt"))

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
    "cloudflareinsights.com",
    "maps.google.com",
]

# Core scripts that must NOT be stubbed, otherwise the page's inline
# submit handler (which shows the success message) never runs.
CORE_JS = (
    "jquery.js",
    "bootstrap.min.js",
    "main.js",
    "subscription.js",
)


def _install_routes(page: Page) -> None:
    def _handler(route):
        url = route.request.url
        try:
            if any(host in url for host in AD_HOSTS):
                route.abort()
                return
            if "automationexercise.com/static/js/" in url:
                if any(core in url for core in CORE_JS):
                    route.continue_()
                    return
                route.fulfill(status=200, content_type="application/javascript", body="")
                return
            route.continue_()
        except Exception:
            try:
                route.continue_()
            except Exception:
                pass

    page.route("**/*", _handler)


def _goto_with_retry(page: Page, url: str, attempts: int = 3) -> None:
    last_error = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="commit", timeout=15000)
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


def test_contact_us_form_submission(page: Page):
    print("Starting TC_006: Verify contact us form submission")

    # Step 1: Navigate to the site and click 'Contact us'
    print("Step 1: Navigating to automationexercise.com and clicking 'Contact us'")
    _goto_with_retry(page, "https://automationexercise.com")

    contact_link = page.locator("a[href='/contact_us']").first
    expect(contact_link).to_be_visible(timeout=30000)
    contact_link.click()

    # Step 2: Fill in form fields
    print("Step 2: Filling in contact form fields")
    name_input = page.locator("input[data-qa='name']")
    expect(name_input).to_be_visible(timeout=30000)
    name_input.fill("TestUser")
    page.locator("input[data-qa='email']").fill("testuser@example.com")
    page.locator("input[data-qa='subject']").fill("Test Subject")
    page.locator("textarea[data-qa='message']").fill("This is a test message")

    # Step 3: Upload a file (optional - using a sample file path)
    print("Step 3: Uploading a file")
    file_input = page.locator("input[type='file']")
    if file_input.count() > 0:
        file_input.first.set_input_files("test_file.txt")

    # Step 4: Click Submit and accept the alert
    print("Step 4: Clicking Submit button")
    submit_button = page.locator("input[data-qa='submit-button']").first
    if submit_button.count() == 0:
        submit_button = page.get_by_role("button", name="Submit").first
    expect(submit_button).to_be_visible(timeout=30000)

    def _accept_dialog(dialog):
        try:
            dialog.accept()
        except Exception:
            pass

    page.once("dialog", _accept_dialog)
    submit_button.click()

    # Step 6: Verify success message
    success_message = page.locator("div.status.alert.alert-success").first
    expect(success_message).to_be_visible(timeout=30000)
    expect(success_message).to_contain_text(
        "Success! Your details have been submitted successfully."
    )
    print("TC_006 completed successfully")
