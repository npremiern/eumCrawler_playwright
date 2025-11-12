"""Debug script to check actual page structure and selectors."""

import time
from playwright.sync_api import sync_playwright

def debug_page():
    """Open the page and print actual selectors."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Navigating to eum.go.kr...")
        page.goto("https://www.eum.go.kr/")
        time.sleep(3)

        # Find search input
        print("\n=== Looking for search input ===")
        try:
            search_input = page.query_selector("#recent > input")
            if search_input:
                print("✓ Found search input: #recent > input")
            else:
                print("✗ Search input not found with #recent > input")
                # Try alternatives
                all_inputs = page.query_selector_all("input")
                print(f"Found {len(all_inputs)} input elements on page")
                for i, inp in enumerate(all_inputs[:5]):
                    print(f"  Input {i}: id='{inp.get_attribute('id')}', class='{inp.get_attribute('class')}'")
        except Exception as e:
            print(f"Error: {e}")

        # Try to search
        test_address = "서울특별시 강남구 테헤란로 152"
        print(f"\n=== Searching for: {test_address} ===")

        try:
            search_input = page.query_selector("#recent > input")
            if search_input:
                search_input.fill(test_address)
                time.sleep(0.5)
                search_input.press("Enter")
                print("Search submitted, waiting for results...")
                time.sleep(5)

                # Check current URL
                print(f"Current URL: {page.url}")

                # Try to find result elements
                print("\n=== Checking for result elements ===")

                selectors_to_check = [
                    "#present_addr",
                    "#present_class",
                    "#present_area",
                    "#jiga",
                    "present_addr",
                    ".present_addr",
                    "[id*='present']",
                    "[id*='addr']",
                ]

                for selector in selectors_to_check:
                    element = page.query_selector(selector)
                    if element:
                        text = element.inner_text()[:50]
                        print(f"✓ Found: {selector} = '{text}'")
                    else:
                        print(f"✗ Not found: {selector}")

                # Get all elements with IDs
                print("\n=== All elements with IDs on result page ===")
                all_with_ids = page.query_selector_all("[id]")
                print(f"Found {len(all_with_ids)} elements with IDs")
                for elem in all_with_ids[:30]:
                    elem_id = elem.get_attribute("id")
                    if elem_id and ("present" in elem_id.lower() or "jiga" in elem_id.lower() or "addr" in elem_id.lower()):
                        try:
                            text = elem.inner_text()[:30].strip()
                            if text:
                                print(f"  ID: {elem_id} = '{text}'")
                        except:
                            pass

                # Save page content for inspection
                print("\n=== Saving page HTML ===")
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("✓ Saved to debug_page.html")

                input("\nPress Enter to close browser...")

        except Exception as e:
            print(f"Error during search: {e}")
            import traceback
            traceback.print_exc()

        browser.close()

if __name__ == "__main__":
    debug_page()
