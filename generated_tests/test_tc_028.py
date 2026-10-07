import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_scroll_up_down_without_arrow_button(page):
    print("Starting TC_028: Verify scroll up/down functionality without arrow button")
    
    # Precondition: Navigate to the site
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    print("Navigated to automationexercise.com")
    
    # Step 1: Scroll down to the bottom of the page
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    print("Scrolled down to the bottom of the page")
    
    # Verify we are at the bottom (optional check)
    scroll_position = page.evaluate("window.scrollY")
    page_height = page.evaluate("document.body.scrollHeight")
    print(f"Current scroll position: {scroll_position}, Page height: {page_height}")
    
    # Step 2: Scroll up manually using the mouse wheel or scrollbar
    # Simulate mouse wheel scroll up (negative deltaY)
    for _ in range(10):
        page.mouse.wheel(0, -1500)
        page.wait_for_timeout(100)  # Scroll up significantly
    print("Scrolled up using mouse wheel")
    
    # Step 3: Verify that the page scrolls up to the top
    # Wait for scroll to reach top (auto-waiting via expect)
    expect(page).to_have_title("Automation Exercise")  # Ensure page is still loaded
    # Check scroll position is near top (0)
    page.wait_for_function("window.scrollY < 10", timeout=10000)
    print("Page scrolled up to the top")
    
    # Step 4: Verify that the header is visible
    header = page.locator("header")
    expect(header).to_be_visible()
    print("Header is visible")
    
    print("TC_028 completed successfully")