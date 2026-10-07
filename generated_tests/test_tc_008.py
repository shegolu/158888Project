import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

def test_verify_all_products_and_product_detail(page):
    print("Starting TC_008: Verify all products and product detail page")
    
    # Step 1: Navigate to the site and click on 'Products' button
    print("Step 1: Navigating to automationexercise.com and clicking Products button")
    page.goto("https://automationexercise.com", wait_until="domcontentloaded", timeout=100000)
    page.locator("a[href='/products']").click()
    
    # Step 2: Verify that the products list is displayed
    print("Step 2: Verifying products list is displayed")
    products_header = page.locator("h2.title.text-center")
    expect(products_header).to_be_visible()
    expect(products_header).to_contain_text("All Products")
    # Verify at least one product is visible
    first_product = page.locator(".features_items .product-image-wrapper").first
    expect(first_product).to_be_visible()
    
    # Step 3: Click on 'View Product' for the first product
    print("Step 3: Clicking on View Product for the first product")
    view_product_button = page.locator("a[href^='/product_details/']").first
    view_product_button.click()
    
    # Step 4: Verify that the product detail page is displayed
    print("Step 4: Verifying product detail page is displayed")
    product_detail = page.locator(".product-details")
    expect(product_detail).to_be_visible()
    
    # Step 5: Verify product name, category, price, availability, condition, brand
    print("Step 5: Verifying product information on detail page")
    product_name = page.locator(".product-details .product-information h2")
    expect(product_name).to_be_visible()
    expect(product_name).not_to_be_empty()
    
    category = page.locator(".product-details .product-information p").first
    expect(category).to_be_visible()
    expect(category).to_contain_text("Category:")
    
    price = page.locator(".product-details .product-information span span")
    expect(price).to_be_visible()
    expect(price).not_to_be_empty()
    
    availability = page.locator(".product-details .product-information p").nth(1)
    expect(availability).to_be_visible()
    expect(availability).to_contain_text("Availability:")
    
    condition = page.locator(".product-details .product-information p").nth(2)
    expect(condition).to_be_visible()
    expect(condition).to_contain_text("Condition:")
    
    brand = page.locator(".product-details .product-information p").nth(3)
    expect(brand).to_be_visible()
    expect(brand).to_contain_text("Brand:")
    
    print("TC_008 completed successfully: All products listed and product detail page shows complete information")