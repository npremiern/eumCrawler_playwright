"""Debug script to check actual image URL."""

import time
from playwright.sync_api import sync_playwright

def debug_image():
    """Check actual image URL."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Navigating to eum.go.kr...")
        page.goto("https://www.eum.go.kr/")
        time.sleep(3)

        # Search
        test_address = "서울특별시 강남구 테헤란로 152"
        print(f"Searching for: {test_address}")

        search_input = page.query_selector("#recent > input")
        if search_input:
            search_input.fill(test_address)
            time.sleep(0.5)
            search_input.press("Enter")
            print("Search submitted, waiting...")
            time.sleep(5)

            # Check for present_mark1
            mark1 = page.query_selector("#present_mark1")
            if mark1:
                print(f"✓ Found present_mark1: {mark1.inner_text()}")

            # Find image element
            print("\n=== Looking for image ===")

            # Try the original selector
            img_selector = "#appoint > div:nth-child(4) > table > tbody > tr:nth-child(1) > td.m_pd0.vtop > div > div > img"
            img = page.query_selector(img_selector)

            if img:
                src = img.get_attribute("src")
                print(f"✓ Found image with selector: {img_selector}")
                print(f"  src attribute: {src}")

                # Try to get the actual URL
                page_url = page.url
                print(f"  Current page URL: {page_url}")

                # Evaluate in browser context to get absolute URL
                abs_url = page.evaluate("""
                    (selector) => {
                        const img = document.querySelector(selector);
                        if (img) {
                            return img.src;  // This gives absolute URL
                        }
                        return null;
                    }
                """, img_selector)
                print(f"  Absolute URL (from browser): {abs_url}")
            else:
                print("✗ Image not found with original selector")

                # Try to find any images
                all_images = page.query_selector_all("img")
                print(f"\n Found {len(all_images)} images on page")

                for i, img in enumerate(all_images[:10]):
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt")
                    if src and ("key=" in src or "image" in src.lower()):
                        print(f"  Image {i}: src='{src}', alt='{alt}'")

            input("\nPress Enter to close...")

        browser.close()

if __name__ == "__main__":
    debug_image()
