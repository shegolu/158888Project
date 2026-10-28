import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_scroll_up_down_with_arrow_button(page: Page):
    print("Starting TC_027: Verify scroll up/down functionality with arrow button")
    
    # Navigate to the site
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    print("Step 0: Navigated to https://automationexercise.com")
    
    # Step 1: Scroll down to the bottom of the page
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)  # small wait for scroll to settle, but not using time.sleep
    print("Step 1: Scrolled down to the bottom of the page")
    
    # Step 2: Click the arrow button to scroll up
    # The arrow button is typically at the bottom right, with id 'scrollUp' or class 'scrollup'
    arrow_button = page.locator("#scrollUp, .scrollup, a[href='#top']")
    arrow_button.first.click()
    print("Step 2: Clicked the arrow button to scroll up")
    
    # Step 3: Verify that the page scrolls up to the top
    # Check that the scroll position is near the top (0)
    page.wait_for_function("window.scrollY === 0")
    print("Step 3: Verified page scrolled up to the top")
    
    # Step 4: Verify that the header is visible
    header = page.locator("header")
    expect(header).to_be_visible()
    print("Step 4: Verified header is visible")
    
    print("TC_027 completed successfully")