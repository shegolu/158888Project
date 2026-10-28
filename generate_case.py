import json
from script_gen import get_client


def generate_test_cases(website_url: str, feature_description: str) -> list:
    """
    Generate structured test cases using DeepSeek LLM.
    Returns a list of test case dictionaries.
    """
    prompt = f"""
    You are a senior QA engineer. Generate a comprehensive test suite for: {website_url}.
    
    The target application is an e-commerce platform with both UI and REST API endpoints.
    
    **REQUIREMENTS:**
    1. Generate test cases covering ALL of the following scenarios. Do not omit any.
    
    **UI Scenarios (must cover):**
    - User registration with valid data (positive)
    - User registration with existing email (negative)
    - User login with correct credentials (positive)
    - User login with incorrect credentials (negative)
    - User logout
    - Contact us form submission
    - Verify test cases page navigation
    - View all products and product detail page
    - Search product with valid keyword (positive)
    - Search product with invalid keyword (negative)
    - Subscription in home page
    - Subscription in cart page
    - Add single product to cart
    - Add multiple products to cart
    - Verify product quantity in cart
    - Remove product from cart
    - Place order: register while checkout
    - Place order: register before checkout
    - Place order: login before checkout
    - View category products
    - View brand products
    - Search products and verify cart after login
    - Add review on product
    - Add to cart from recommended items
    - Verify address details in checkout page
    - Download invoice after purchase
    - Scroll up/down functionality (with and without arrow button)
    
    **API Scenarios (must cover):**
    - GET all products list
    - POST to all products list (method not allowed)
    - GET all brands list
    - PUT to all brands list (method not allowed)
    - POST to search product with search_product parameter
    - POST to search product without search_product parameter
    - POST to verify login with valid credentials
    - POST to verify login without email parameter
    - DELETE to verify login (method not allowed)
    - POST to verify login with invalid credentials
    - POST to create/register user account
    - DELETE to delete user account
    - PUT to update user account
    - GET user account detail by email
    
    2. Output ONLY valid JSON. Do not add any markdown, explanations, or code blocks.
    
    3. Use the following JSON structure EXACTLY:
    [
        {{
            "test_id": "TC_001",
            "test_name": "Descriptive name of the test",
            "test_type": "UI" or "API",
            "preconditions": "What needs to be set up before the test",
            "test_steps": [
                "Step 1: Action description",
                "Step 2: Action description"
            ],
            "expected_result": "Expected outcome after execution"
        }}
    ]
    
    4. Ensure the JSON is valid and parsable. Do not wrap it in backticks.
    5. Use realistic test data (e.g., testuser@example.com, Test@123).
    6. For API tests, use the exact endpoints from automationexercise.com API documentation.
    7. Generate approximately 35-40 test cases in total to cover all scenarios above.
    
    
    Generate the test cases now.
    """

    try:
        response = get_client().chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a senior QA engineer. Output pure valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            stream=False
        )

        content = response.choices[0].message.content.strip()

        # Clean markdown code blocks if the AI accidentally includes them
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        test_cases = json.loads(content)
        return test_cases

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON response: {e}")
        print(f"[DEBUG] Raw response: {content}")
        return []
    except Exception as e:
        print(f"[ERROR] Failed to generate test cases: {e}")
        return []


if __name__ == "__main__":
    print("[INFO] Generating test cases via DeepSeek AI...")

    cases = generate_test_cases(
        website_url="https://automationexercise.com",
        feature_description="User registration, login, product search, shopping cart, checkout flow, and public REST API endpoints (product listing, login verification, account management)"
    )

    if not cases:
        print("[ERROR] No test cases generated. Please check your API key and network.")
        exit(1)

    output_file = "generated_test_cases.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Generated {len(cases)} test cases. Saved to {output_file}")

    if cases:
        print("\n[PREVIEW] First test case:")
        print(json.dumps(cases[0], indent=2, ensure_ascii=False))
