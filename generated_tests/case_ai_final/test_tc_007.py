import pytest
from playwright.sync_api import Page, expect


def _route_page_assets(route):
    """Keep the public demo usable when its own JS/CDN assets hang."""
    url = route.request.url
    host = url.split("/")[2] if "://" in url else ""
    if any(domain in host for domain in (
        "googlesyndication.com", "doubleclick.net", "googleadservices.com",
        "fundingchoicesmessages.google.com", "googletagservices.com",
        "adtrafficquality.google", "googletagmanager.com",
    )):
        route.abort()
        return
    if "automationexercise.com/static/js/" in url:
        route.fulfill(status=200, content_type="application/javascript", body="")
        return
    route.continue_()


@pytest.fixture(scope="function")
def browser_context(page: Page):
    print("Setting up browser context")
    page.route("**/*", _route_page_assets)
    last_error = None
    for attempt in range(3):
        try:
            page.goto("https://automationexercise.com", wait_until="commit", timeout=60000)
            break
        except Exception as exc:
            last_error = exc
            page.wait_for_timeout(1000)
    else:
        raise last_error
    page.locator("header a[href='/test_cases']").wait_for(state="visible", timeout=30000)
    yield page
    print("Tearing down browser context")
    page.close()

def test_verify_test_cases_page_navigation(browser_context: Page):
    page = browser_context
    print("Starting TC_007: Verify test cases page navigation")
    
    # Step 1: Click on 'Test Cases' button
    print("Step 1: Clicking on 'Test Cases' button")
    test_cases_button = page.locator("header a[href='/test_cases']")
    test_cases_button.click(no_wait_after=True, force=True)
    page.wait_for_url("https://automationexercise.com/test_cases", wait_until="commit", timeout=30000)
    
    # Step 2: Verify that the user is navigated to the test cases page
    print("Step 2: Verifying navigation to test cases page")
    assert page.url == "https://automationexercise.com/test_cases"
    
    # Step 3: Verify that the page displays test cases
    print("Step 3: Verifying test cases are displayed")
    test_cases_header = page.locator("h2.title.text-center", has_text="Test Cases")
    expect(test_cases_header).to_be_visible()
    expect(test_cases_header).to_contain_text("Test Cases")
    
    # Additional verification that test cases content is present
    test_cases_section = page.locator("div.panel-group").first
    expect(test_cases_section).to_be_visible()
    
    print("TC_007 completed successfully: User navigated to test cases page and test cases are displayed")
