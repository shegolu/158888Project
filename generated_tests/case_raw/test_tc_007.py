import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def browser_context(page: Page):
    print("Setting up browser context")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    yield page
    print("Tearing down browser context")
    page.close()

def test_verify_test_cases_page_navigation(browser_context: Page):
    page = browser_context
    print("Starting TC_007: Verify test cases page navigation")
    
    # Step 1: Click on 'Test Cases' button
    print("Step 1: Clicking on 'Test Cases' button")
    test_cases_button = page.locator("a[href='/test_cases']")
    test_cases_button.click()
    
    # Step 2: Verify that the user is navigated to the test cases page
    print("Step 2: Verifying navigation to test cases page")
    expect(page).to_have_url("https://automationexercise.com/test_cases")
    
    # Step 3: Verify that the page displays test cases
    print("Step 3: Verifying test cases are displayed")
    test_cases_header = page.locator("h2.title.text-center")
    expect(test_cases_header).to_be_visible()
    expect(test_cases_header).to_contain_text("Test Cases")
    
    # Additional verification that test cases content is present
    test_cases_section = page.locator("div.panel-group")
    expect(test_cases_section).to_be_visible()
    
    print("TC_007 completed successfully: User navigated to test cases page and test cases are displayed")