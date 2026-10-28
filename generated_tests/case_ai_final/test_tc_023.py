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


def _route_handler(route):
    url = route.request.url
    if any(host in url for host in AD_HOSTS):
        route.abort()
        return
    if "automationexercise.com/static/js/" in url:
        route.fulfill(status=200, content_type="application/javascript", body="")
        return
    route.continue_()


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    page.route("**/*", _route_handler)
    yield page
    context.close()


def _goto_with_retry(page: Page, url: str, ready_locator: str, attempts: int = 3) -> None:
    last_error = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="commit", timeout=15000)
            page.locator(ready_locator).first.wait_for(state="visible", timeout=20000)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if last_error is not None:
        raise last_error


def test_verify_add_review_on_product(page: Page):
    print("Starting TC_023: Verify add review on product")

    # Step 1: Navigate to the site and click on 'Products' button
    print("Step 1: Navigating to automationexercise.com and clicking 'Products'")
    _goto_with_retry(page, "https://automationexercise.com", "a[href='/products']")

    page.locator("a[href='/products']").first.click()
    page.locator(".features_items .product-image-wrapper").first.wait_for(
        state="visible", timeout=20000
    )

    # Step 2: Click 'View Product' for the first product
    print("Step 2: Clicking 'View Product' for the first product")
    view_product_link = (
        page.locator(".features_items .product-image-wrapper")
        .first.locator("a[href*='/product_details']")
    )
    view_product_link.first.wait_for(state="attached", timeout=20000)
    product_href = view_product_link.first.get_attribute("href")
    product_url = (
        product_href
        if product_href.startswith("http")
        else "https://automationexercise.com" + product_href
    )
    _goto_with_retry(page, product_url, "#review-section")

    # Step 3: Scroll to the review section
    print("Step 3: Scrolling to the review section")
    review_section = page.locator("#review-section")
    review_section.wait_for(state="visible", timeout=20000)
    review_section.scroll_into_view_if_needed()

    # Step 4: Fill in the review form
    print("Step 4: Filling in review form with name, email, and review")
    page.locator("#name").wait_for(state="visible", timeout=20000)
    page.locator("#name").fill("TestUser")
    page.locator("#email").fill("testuser@example.com")
    page.locator("#review").fill("Great product!")

    # Step 5: Click 'Submit' button
    print("Step 5: Clicking 'Submit' button")
    submit_button = page.locator("#button-review")
    submit_button.wait_for(state="visible", timeout=20000)
    submit_button.click()

    # Step 6: Verify success message
    print("Step 6: Verifying success message")
    success_message = page.locator(".alert-success")
    expect(success_message).to_be_visible()
    expect(success_message).to_contain_text("Thank you for your review.")

    print("TC_023 completed successfully")