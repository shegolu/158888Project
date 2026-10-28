import pytest
from playwright.sync_api import Page, expect
import os
print("Current dir:", os.getcwd())
print("File exists?", os.path.exists("test_file.txt"))


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_contact_us_form_submission(page: Page):
    print("Starting TC_006: Verify contact us form submission")
    
    # Step 1: Navigate to the site and click 'Contact us'
    print("Step 1: Navigating to automationexercise.com and clicking 'Contact us'")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    page.locator("a[href='/contact_us']").click()
    
    # Step 2: Fill in form fields
    print("Step 2: Filling in contact form fields")
    page.locator("input[data-qa='name']").fill("TestUser")
    page.locator("input[data-qa='email']").fill("testuser@example.com")
    page.locator("input[data-qa='subject']").fill("Test Subject")
    page.locator("textarea[data-qa='message']").fill("This is a test message")
    
    # Step 3: Upload a file (optional - using a sample file path)
    print("Step 3: Uploading a file")
    page.locator("input[type='file']").set_input_files("test_file.txt")  # Ensure this file exists or adjust path
    
    # Step 4: Click Submit
    print("Step 4: Clicking Submit button")
    submit_button = page.get_by_role("button", name="Submit")
    expect(submit_button).to_be_visible()
    submit_button.click()
    print("TC_006 completed successfully")