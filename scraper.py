"""Web scraping logic using Playwright."""

import os
import time
import base64
from pathlib import Path
from typing import Optional, Dict
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from config import (
    BASE_URL,
    SELECTORS,
    DEFAULT_WAIT_TIME,
    PAGE_LOAD_TIMEOUT,
    MAX_RETRIES,
    TEMP_IMAGE_DIR,
    IMAGES_DIR,
)

console = Console()


class RealEstateScraper:
    """Scraper for real estate information from eum.go.kr."""

    def __init__(self, headless: bool = True, wait_time: float = DEFAULT_WAIT_TIME):
        """
        Initialize the scraper.

        Args:
            headless: Whether to run browser in headless mode
            wait_time: Time to wait after page loads (seconds)
        """
        self.headless = headless
        self.wait_time = wait_time
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # Create temp and permanent image directories
        Path(TEMP_IMAGE_DIR).mkdir(exist_ok=True)
        Path(IMAGES_DIR).mkdir(exist_ok=True)

    def start(self) -> bool:
        """
        Start the browser.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            self.page.set_default_timeout(PAGE_LOAD_TIMEOUT)
            console.print("[green]OK[/green] Browser started")
            return True
        except Exception as e:
            console.print(f"[red]Error starting browser: {e}[/red]")
            console.print("[yellow]Hint: Run 'playwright install chromium' to install browser[/yellow]")
            return False

    def search_address(self, address: str) -> bool:
        """
        Search for an address on the website.

        Args:
            address: Address to search

        Returns:
            True if search was successful, False otherwise
        """
        retries = 0
        while retries < MAX_RETRIES:
            try:
                # Navigate to the website
                console.print(f"[cyan]Navigating to {BASE_URL}[/cyan]")
                self.page.goto(BASE_URL, wait_until="domcontentloaded")
                time.sleep(self.wait_time)

                # Find and fill search input
                search_input = self.page.wait_for_selector(SELECTORS["SEARCH_INPUT"], timeout=10000)
                search_input.fill(address)
                time.sleep(0.5)

                # Press Enter to search
                search_input.press("Enter")
                console.print(f"[cyan]Searching for: {address}[/cyan]")

                # Wait for results to load dynamically (increased timeout)
                # The page doesn't navigate, results load in-place
                time.sleep(self.wait_time)

                # Check if result page loaded with longer timeout
                # Using PRESENT_MARK1 as indicator for successful search
                try:
                    console.print("[cyan]Waiting for search results...[/cyan]")
                    self.page.wait_for_selector(SELECTORS["PRESENT_MARK1"], timeout=15000)
                    # Extra wait to ensure all data is loaded
                    time.sleep(1)
                    console.print("[green]OK[/green] Search results loaded")
                    return True
                except PlaywrightTimeoutError:
                    console.print(f"[yellow]Warning: No results found for address: {address}[/yellow]")
                    return False

            except Exception as e:
                retries += 1
                console.print(f"[yellow]Attempt {retries}/{MAX_RETRIES} failed: {e}[/yellow]")
                if retries < MAX_RETRIES:
                    console.print(f"[cyan]Retrying in {self.wait_time} seconds...[/cyan]")
                    time.sleep(self.wait_time)
                else:
                    console.print(f"[red]Failed to search address after {MAX_RETRIES} attempts[/red]")
                    return False

        return False

    def extract_data(self) -> Dict[str, str]:
        """
        Extract data from the current page.

        Returns:
            Dictionary with extracted data
        """
        data = {}

        # Extract text data
        for key, selector in SELECTORS.items():
            if key == "IMAGE":
                continue  # Handle images separately

            try:
                element = self.page.query_selector(selector)
                if element:
                    text = element.inner_text().strip()
                    data[key.lower()] = text
                else:
                    console.print(f"[yellow]Warning: Element not found for {key}[/yellow]")
                    data[key.lower()] = ""
            except Exception as e:
                console.print(f"[yellow]Warning: Error extracting {key}: {e}[/yellow]")
                data[key.lower()] = ""

        return data

    def download_image(self, row: int, address: str) -> Optional[str]:
        """
        Download image from the current page.

        Args:
            row: Row number for naming the image file
            address: Address string for permanent filename

        Returns:
            Path to downloaded image or None if failed
        """
        try:
            # Get absolute image URL using browser evaluation
            # This ensures we get the correct absolute URL
            img_url = self.page.evaluate("""
                (selector) => {
                    const img = document.querySelector(selector);
                    if (img && img.src) {
                        return img.src;  // Browser returns absolute URL
                    }
                    return null;
                }
            """, SELECTORS["IMAGE"])

            if not img_url:
                console.print("[yellow]Warning: Image element or URL not found[/yellow]")
                return None

            console.print(f"[cyan]Downloading image from: {img_url}[/cyan]")

            # Save image path
            image_path = os.path.join(TEMP_IMAGE_DIR, f"row_{row}.png")

            # Download image using Playwright (maintains session/cookies)
            # This is necessary because the server requires authentication
            img_data = self.page.evaluate("""
                async (url) => {
                    const response = await fetch(url);
                    const blob = await response.blob();
                    const reader = new FileReader();
                    return new Promise((resolve) => {
                        reader.onloadend = () => {
                            // Return base64 data without the data URL prefix
                            resolve(reader.result.split(',')[1]);
                        };
                        reader.readAsDataURL(blob);
                    });
                }
            """, img_url)

            if not img_data:
                console.print("[yellow]Warning: No image data received from browser[/yellow]")
                return None

            # Decode base64 and save
            img_bytes = base64.b64decode(img_data)

            # Verify it's a valid image before saving
            try:
                img = Image.open(BytesIO(img_bytes))
                img.verify()

                # Save to temp file (for Excel insertion)
                with open(image_path, "wb") as f:
                    f.write(img_bytes)

                # Also save to permanent images folder with address-based filename
                # Replace spaces with underscores and remove special characters
                safe_filename = address.replace(" ", "_")
                safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ("_", "-"))
                permanent_path = os.path.join(IMAGES_DIR, f"{safe_filename}.png")

                # If file exists, append row number to make unique
                if os.path.exists(permanent_path):
                    permanent_path = os.path.join(IMAGES_DIR, f"{safe_filename}_row{row}.png")

                with open(permanent_path, "wb") as f:
                    f.write(img_bytes)

                console.print(f"[green]OK[/green] Image downloaded: {image_path}")
                console.print(f"[green]OK[/green] Saved to: {permanent_path}")
                return image_path
            except Exception as verify_error:
                console.print(f"[yellow]Warning: Downloaded data is not a valid image: {verify_error}[/yellow]")
                return None

        except Exception as e:
            console.print(f"[yellow]Warning: Error downloading image: {e}[/yellow]")
            return None

    def scrape_address(self, address: str, row: int) -> Optional[Dict[str, str]]:
        """
        Complete scraping process for one address.

        Args:
            address: Address to search
            row: Row number for image naming

        Returns:
            Dictionary with scraped data including image path, or None if failed
        """
        if not self.search_address(address):
            return None

        # Extract data
        data = self.extract_data()

        # Download image (pass address for permanent filename)
        image_path = self.download_image(row, address)
        if image_path:
            data["image_path"] = image_path

        return data

    def close(self):
        """Close the browser and cleanup."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        console.print("[green]OK[/green] Browser closed")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
