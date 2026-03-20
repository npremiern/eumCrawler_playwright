"""Web scraping logic using Playwright."""

import os
import time
import base64
from pathlib import Path
from typing import Optional, Dict
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin
import sys

from config import (
    BASE_URL,
    SELECTORS,
    DEFAULT_WAIT_TIME,
    PAGE_LOAD_TIMEOUT,
    MAX_RETRIES,
    TEMP_IMAGE_DIR,
    IMAGES_DIR,
    IMAGE_WIDTH,
    PDF_DIR,
)
from console_helper import console


class RealEstateScraper:
    """Scraper for real estate information from eum.go.kr."""

    def __init__(self, headless: bool = True, wait_time: float = DEFAULT_WAIT_TIME, log_callback=None):
        """
        Initialize the scraper.

        Args:
            headless: Whether to run browser in headless mode
            wait_time: Time to wait after page loads (seconds)
            log_callback: Optional callback for logging messages
        """
        self.headless = headless
        self.wait_time = wait_time
        self.log_callback = log_callback
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context = None  # Add browser context
        self.page: Optional[Page] = None
        self.popup_page: Optional[Page] = None

        # Create temp and permanent image directories
        Path(TEMP_IMAGE_DIR).mkdir(exist_ok=True)
        Path(IMAGES_DIR).mkdir(exist_ok=True)
        Path(PDF_DIR).mkdir(exist_ok=True)

    def log(self, message):
        """Log message using callback or console."""
        if self.log_callback:
            self.log_callback(message)
        else:
            console.print(message)

    def start(self) -> bool:
        """
        Start the browser.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context()  # Create context explicitly
            self.page = self.context.new_page()  # Create page from context
            self.page.set_default_timeout(PAGE_LOAD_TIMEOUT)
            
            # Navigate to BASE_URL immediately
            self.log(f"[cyan]Navigating to {BASE_URL}...[/cyan]")
            self.page.goto(BASE_URL, wait_until="domcontentloaded")
            
            self.log("[green]OK[/green] Browser started and navigated to eum.go.kr")
            return True
        except Exception as e:
            self.log(f"[red]Error starting browser: {e}[/red]")
            self.log("[yellow]Hint: Run 'playwright install chromium' to install browser[/yellow]")
            return False

    def check_address_count(self, address: str, verbose: bool = False) -> tuple[int, Optional[str]]:
        """
        Check the number of search results for an address using Ajax.
        
        Args:
            address: Address to check
            verbose: Whether to log detailed response
            
        Returns:
            Tuple of (count, pnu). PNU is None if count != 1 or not found.
            Returns (-1, None) on error.
        """
        try:
            # Ensure we are on the domain to have cookies
            if "eum.go.kr" not in self.page.url:
                self.page.goto(BASE_URL, wait_until="domcontentloaded")
                
            ajax_url = "https://www.eum.go.kr/web/am/mp/mpSearchAddrAjaxXml.jsp"
            response = self.page.request.post(
                ajax_url,
                form={
                    "sId": "selectAdAddrList",
                    "keyword": address
                },
                headers={
                    "Referer": BASE_URL,
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://www.eum.go.kr",
                    "Accept": "application/json, text/javascript, */*; q=0.01"
                }
            )
            
            if response.status == 200:
                # Handle encoding explicitly (likely EUC-KR for Korean gov sites)
                body_bytes = response.body()
                try:
                    decoded_text = body_bytes.decode('euc-kr')
                except UnicodeDecodeError:
                    try:
                        decoded_text = body_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fallback to ignore errors if both fail
                        decoded_text = body_bytes.decode('euc-kr', errors='ignore')
                
                xml_text = decoded_text
                
                # Check if it's JSON wrapping XML
                import json
                try:
                    json_data = json.loads(decoded_text)
                    # Look for XML string in values
                    if isinstance(json_data, dict):
                        for key, value in json_data.items():
                            if isinstance(value, str) and value.strip().startswith("<?xml"):
                                xml_text = value
                                break
                except json.JSONDecodeError:
                    # Not JSON, assume it's raw XML
                    pass
                
                # Try to parse XML
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(xml_text)
                except Exception as parse_error:
                    self.log(f"[red]XML Parsing Error: {parse_error}[/red]")
                    # Log the response content to help debugging (it might be HTML error page)
                    self.log(f"[dim]Response content (first 500 chars): {decoded_text[:500]}[/dim]")
                    return -1, None
                
                if verbose:
                    self.log(f"[dim]XML Content: {xml_text}[/dim]")

                # Find items (support both <list> and <node>)
                items = root.findall('.//list')
                if not items:
                    items = root.findall('.//node')
                
                count = len(items)
                
                pnu = None
                if count >= 1:
                    # Use the first result if multiple exist
                    pnu_elem = items[0].find('pnu')
                    if pnu_elem is not None:
                        pnu = pnu_elem.text
                
                return count, pnu
            else:
                self.log(f"[yellow]Warning: Pre-check failed with status {response.status}[/yellow]")
                return -1, None
                
        except Exception as e:
            self.log(f"[yellow]Warning: Error in address pre-check: {e}[/yellow]")
            return -1, None

    def search_address(self, address: str, pnu: str = None, scale: str = "1200") -> tuple[bool, str]:
        """
        Search for an address on the website.
        Assumes address has been validated to have 1 result.

        Args:
            address: Address to search

        Returns:
            Tuple of (success, message)
        """
        retries = 0
        last_error = ""
        while retries < MAX_RETRIES:
            try:
                # CRITICAL: Always navigate to MAIN PAGE before searching.
                # This prevents "stale data" where the previous search result is scraped again.
                # Without this, row 2 might scrape row 1's data if the page doesn't update fast enough.
                console.print(f"[cyan]Refreshing page to prevent duplicate data...[/cyan]")
                self.page.goto(BASE_URL, wait_until="domcontentloaded")
                time.sleep(1.0) # Wait for input field to be ready

                # Find and fill search input
                try:
                    search_input = self.page.wait_for_selector(SELECTORS["SEARCH_INPUT"], timeout=5000)
                except:
                    # If selector not found, try reloading
                    self.page.goto(BASE_URL, wait_until="domcontentloaded")
                    search_input = self.page.wait_for_selector(SELECTORS["SEARCH_INPUT"], timeout=10000)
                    
                search_input.fill(address)
                time.sleep(0.5)

                # Set Scale and scaleFlag before pressing Enter or clicking
                log_data = self.page.evaluate(f"""
                    () => {{
                        let updated = 0;
                        document.querySelectorAll('[name="scale"]').forEach(e => {{ e.value = '{scale}'; updated++; }});
                        document.querySelectorAll('[name="scaleFlag"]').forEach(e => {{ e.value = 'Y'; updated++; }});
                        
                        document.querySelectorAll('form').forEach(form => {{
                            if (!form.querySelector('[name="scale"]')) {{
                                let s = document.createElement('input'); s.type='hidden'; s.name='scale'; s.value='{scale}'; form.appendChild(s);
                                updated++;
                            }}
                            if (!form.querySelector('[name="scaleFlag"]')) {{
                                let sf = document.createElement('input'); sf.type='hidden'; sf.name='scaleFlag'; sf.value='Y'; form.appendChild(sf);
                                updated++;
                            }}
                        }});
                        return updated + " elements updated before search";
                    }}
                """)
                self.log(f"Form values set (Enter): {log_data}")

                # Press Enter to trigger search
                search_input.press("Enter")
                console.print(f"[cyan]Searching for: {address}[/cyan]")

                # Wait for dropdown results or direct navigation
                time.sleep(1.5)

                # Check if dropdown with multiple results appeared
                # Selector for the first item in the autocomplete dropdown
                first_result_selector = "#recent > div.recent_list.addrDiv > div > ul > li:nth-child(1) > a"
                
                try:
                    # Try to find the dropdown list
                    first_result = self.page.query_selector(first_result_selector)
                    # Set scale and scaleFlag again
                    log_data_click = self.page.evaluate(f"""
                        () => {{
                            let updated = 0;
                            document.querySelectorAll('[name="scale"]').forEach(e => {{ e.value = '{scale}'; updated++; }});
                            document.querySelectorAll('[name="scaleFlag"]').forEach(e => {{ e.value = 'Y'; updated++; }});
                            
                            return updated + " elements updated before click";
                        }}
                    """)
                    self.log(f"Form values set (Click): {log_data_click}")                    
                    if first_result:
                        console.print("[cyan]Multiple results found, clicking first item...[/cyan]")
                        first_result.click()
                        time.sleep(1.5)  # Wait for navigation after click
                except Exception as e:
                    console.print(f"[dim]No dropdown or already navigated: {e}[/dim]")

                # Check if result page loaded
                # Using JIGA as indicator for successful search
                try:
                    console.print("[cyan]Waiting for search results...[/cyan]")
                    self.page.wait_for_selector(SELECTORS["JIGA"], timeout=15000)
                    # Extra wait to ensure all data is loaded
                    time.sleep(1)
                    console.print("[green]OK[/green] Search results loaded")
                    return True, "성공"
                except PlaywrightTimeoutError:
                    msg = f"결과 없음 (Timeout) - {address}"
                    console.print(f"[yellow]Warning: {msg}[/yellow]")
                    return False, msg

            except Exception as e:
                retries += 1
                
                # 오류 메시지 간소화 (첫 줄만 가져오기 및 타임아웃 메시지 직관적으로 변경)
                error_str = str(e).split('\n')[0]
                if "Timeout" in error_str:
                    error_str = "웹페이지 응답 지연 (검색창 접근 시간 초과)"
                
                last_error = error_str
                console.print(f"[yellow]Attempt {retries}/{MAX_RETRIES} failed: {last_error}[/yellow]")
                
                if retries < MAX_RETRIES:
                    console.print(f"[cyan]Retrying in {self.wait_time} seconds...[/cyan]")
                    time.sleep(self.wait_time)
                else:
                    msg = f"최대 접속 재시도 횟수 초과: {last_error}"
                    console.print(f"[red]{msg}[/red]")
                    return False, msg

        return False, f"검색 실패: {last_error}"

    def extract_data(self) -> Dict[str, str]:
        """
        Extract data from the current page.

        Returns:
            Dictionary with extracted data
        """
        data = {}

        # Extract text data
        for key, selector in SELECTORS.items():
            # Skip non-data fields (images, buttons, inputs)
            if key in ["IMAGE", "SEARCH_INPUT", "PRINT_BTN", "PRINT_POPUP_BTN"]:
                continue

            try:
                self.log(f"[dim cyan]Trying to extract {key} with selector: {selector[:50]}...[/dim cyan]")
                element = self.page.query_selector(selector)
                if element:
                    text = element.inner_text().strip()
                    # Retry if empty
                    if not text:
                        time.sleep(0.5)
                        text = element.inner_text().strip()
                    
                    # Clean PRESENT_CLASS (지목): remove ? and extra spaces
                    if key == "PRESENT_CLASS":
                        text = text.replace("?", "").strip()
                    
                    # Parse JIGA to extract year
                    if key == "JIGA":
                        import re
                        # Extract year from format like "67,300,000원 (2025/01)   연도별보기"
                        year_match = re.search(r'\((\d{4}/\d{2})\)', text)
                        if year_match:
                            data["jiga_year"] = year_match.group(1)
                            # Remove year and extra text from jiga
                            text = re.sub(r'\s*\(.*?\).*', '', text).strip()
                        
                    data[key.lower()] = text
                    self.log(f"[green]✓[/green] Extracted {key}: '{text[:50]}...' ")
                else:
                    self.log(f"[yellow]✗ Element not found for {key}[/yellow]")
                    data[key.lower()] = ""
            except Exception as e:
                self.log(f"[red]✗ Error extracting {key}: {e}[/red]")
                data[key.lower()] = ""
                
        return data


    def download_image_from_popup(self, row: int, address: str, pnu: str, scale: str, 
                                  debug_mode: bool = False, step_event = None) -> Optional[str]:
        """
        축척이 1/1200이 아닐 때(예: 600, 3000 등) 사용되는 이미지 전용 다운로드 로직.
        토지이음의 메인 결과화면은 항상 기본 1200 축척으로 지도를 초기화하는 특성이 있습니다. 
        따라서 다른 축척의 지도를 캡처하려면 'luLandPop.jsp'라는 지도 전용 팝업창을 새 탭으로 띄워야 합니다.
        이 함수는 해당 팝업을 열어 지정된 축척이 제대로 적용된 지도를 이미지(png)로 다운받아 저장합니다.
        
        Args:
            row: 엑셀 행 번호
            address: 주소 문자열
            pnu: PNU 코드 (팝업 URL 생성을 위한 필수 고유번호)
            scale: 변경할 축척 (예: "600", "3000")
            debug_mode: 디버그 모드 플래그
            step_event: 대기 이벤트
            
        Returns:
            저장된 이미지 경로 또는 실패 시 None
        """
        try:
            # Construct popup URL
            popup_url = f"https://www.eum.go.kr/web/ar/lu/luLandPop.jsp?pnu={pnu}&sMode=search&default_scale=3000&scale={scale}"
            
            if debug_mode and step_event:
                self.log(f"\n[bold yellow]DEBUG: 팝업 창 띄우기 전 대기 (축적: 1/{scale})[/bold yellow]")
                self.log("[dim]Waiting for user to press 'Next'...[/dim]")
                step_event.wait()
                step_event.clear()
                self.log("[dim]Resuming...[/dim]\n")
            
            self.log(f"[cyan]Navigating popup tab: {popup_url}[/cyan]")
            
            # Reuse or create popup page
            if not self.popup_page or self.popup_page.is_closed():
                self.log("[dim]Creating new popup tab...[/dim]")
                self.popup_page = self.context.new_page()
            
            # Navigate
            self.popup_page.goto(popup_url, wait_until="domcontentloaded")
            time.sleep(1.0) # Wait for image to load
            
            img_selector = "body > form > div > div.big_aC > img"
            img_url = self.popup_page.evaluate(f"""
                () => {{
                    const img = document.querySelector('{img_selector}');
                    if (img && img.src) {{
                        return img.src;
                    }}
                    return null;
                }}
            """)
            
            if not img_url:
                self.log(f"[yellow]Warning: Image element not found in popup for row {row}[/yellow]")
                return None
                
            # Download image
            if not img_url.startswith("http"):
                img_url = BASE_URL.rstrip("/") + "/" + img_url.lstrip("/")
                
            # Use popup_page request
            response = self.popup_page.request.get(img_url)
            if response.status == 200:
                image_data = response.body()
                
                # Save to temp file
                filename = f"row_{row}_{int(time.time())}.png"
                filepath = os.path.join(TEMP_IMAGE_DIR, filename)
                
                with open(filepath, "wb") as f:
                    f.write(image_data)
                    
                # Verify image
                try:
                    with Image.open(filepath) as img:
                        img.verify()
                    
                    # Re-open for format conversion if needed
                    with Image.open(filepath) as img:
                        # Save as PNG if not already
                        if img.format != 'PNG':
                            img.save(filepath, 'PNG')

                        # Also save to permanent images folder with address-based filename
                        # Sanitize filename
                        safe_filename = address.replace(" ", "_")
                        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ("_", "-"))
                        
                        # Filename format: {row}_{address}_{scale}
                        base_filename = f"{row}_{safe_filename}_{scale}"
                        permanent_path = os.path.join(IMAGES_DIR, f"{base_filename}.png")

                        # Check for duplicates and increment suffix
                        if os.path.exists(permanent_path):
                            counter = 1
                            while True:
                                new_path = os.path.join(IMAGES_DIR, f"{base_filename}_{counter}.png")
                                if not os.path.exists(new_path):
                                    permanent_path = new_path
                                    break
                                counter += 1

                        # Save copy to permanent location
                        img.save(permanent_path, 'PNG')
                        w, h = img.size
                        size_kb = os.path.getsize(permanent_path) / 1024
                        self.log(f"[green]OK[/green] Saved popup image: {w}x{h} ({size_kb:.1f}KB)")
                        self.log(f"[dim]Saved to: {permanent_path}[/dim]")
                        
                    return permanent_path
                except Exception as e:
                    self.log(f"[red]Error verifying/processing image: {e}[/red]")
                    return None
            else:
                self.log(f"[red]Failed to download image: Status {response.status}[/red]")
                return None
                
        except Exception as e:
            self.log(f"[red]Error downloading image from popup: {e}[/red]")
            return None

    def download_image(self, row: int, address: str, scale: str = "1200") -> Optional[str]:
        """
        축척이 1/1200(기본값)일 때 사용되는 일반 지적도 이미지 다운로드 로직.
        팝업을 띄우지 않고, 현재 주소 검색이 완료된 메인 결과 화면에 떠 있는 지도의 소스(src)를 
        가져와 이미지를 캡처하여 파일로 저장합니다. 
        인증 세션 정보 유지를 위해 브라우저 세션 내부에서 직접 fetch를 수행합니다.

        Args:
            row: 엑셀 행 번호 (이미지 파일명 작성용)
            address: 주소 문자열 (이미지 파일명 영구 저장용)
            scale: 지도 축척 (기본 "1200")

        Returns:
            다운로드된 이미지 경로 또는 실패 시 None
        """
        try:
            try:
                # 1. Wait for image to be present (max 3 seconds)
                self.page.wait_for_selector(SELECTORS["IMAGE"], timeout=3000)
            except:
                pass

            # 2. Try to find image with primary selector, then fallback to partial match
            result = self.page.evaluate("""
                (selector) => {
                    const debug = [];
                    debug.push(`Trying selector: ${selector}`);
                    
                    // Try exact selector first
                    let img = document.querySelector(selector);
                    if (img) {
                         debug.push("Primary selector found element");
                         if (img.src) {
                             debug.push(`Src found: ${img.src.substring(0, 50)}...`);
                             return { found: true, src: img.src, method: "primary", logs: debug };
                         } else {
                             debug.push("Primary element has no src attribute");
                         }
                    } else {
                        debug.push("Primary selector returned null");
                    }
                    
                    // Fallback: Look for image inside #appoint with 'images?key=' in src
                    debug.push("Trying fallback search...");
                    const candidates = document.querySelectorAll('#appoint img');
                    debug.push(`Found ${candidates.length} candidates in #appoint`);
                    
                    for (const c of candidates) {
                        if (c.src && c.src.includes('images?key=')) {
                            return { found: true, src: c.src, method: "fallback", logs: debug };
                        }
                    }
                    
                    return { found: false, src: null, method: "none", logs: debug };
                }
            """, SELECTORS["IMAGE"])

            # Print JS logs
            if "logs" in result:
                for log_msg in result["logs"]:
                    self.log(f"[dim]JS: {log_msg}[/dim]")

            if not result["found"] or not result["src"]:
                console.print(f"[yellow]Warning: Image element not found (Selector: {SELECTORS['IMAGE']})[/yellow]")
                return None
            
            img_url = result["src"]

            # Resolve relative URL to absolute URL using current page URL
            # This handles cases where src is like "images?key=..."
            img_url = urljoin(self.page.url, img_url)

            console.print(f"[cyan]Downloading image from: {img_url}[/cyan]")

            # Save image path
            image_path = os.path.join(TEMP_IMAGE_DIR, f"row_{row}.png")

            # Download image using Playwright (maintains session/cookies)
            # This is necessary because the server requires authentication
            try:
                img_data_result = self.page.evaluate("""
                    async (url) => {
                        try {
                            const response = await fetch(url);
                            if (!response.ok) {
                                return { success: false, error: `Fetch failed with status ${response.status}` };
                            }
                            const blob = await response.blob();
                            return new Promise((resolve) => {
                                const reader = new FileReader();
                                reader.onloadend = () => {
                                    // Return base64 data without the data URL prefix
                                    const base64data = reader.result.split(',')[1];
                                    resolve({ success: true, data: base64data });
                                };
                                reader.onerror = () => {
                                    resolve({ success: false, error: "FileReader failed" });
                                };
                                reader.readAsDataURL(blob);
                            });
                        } catch (err) {
                            return { success: false, error: err.toString() };
                        }
                    }
                """, img_url)

                if not img_data_result.get("success"):
                    console.print(f"[yellow]Warning: Failed to fetch image data: {img_data_result.get('error')}[/yellow]")
                    return None
                    
                img_data = img_data_result.get("data")
                
            except Exception as eval_error:
                 console.print(f"[red]Error executing fetch script: {eval_error}[/red]")
                 return None

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
                
                # Filename format: {row}_{address}_{scale}
                base_filename = f"{row}_{safe_filename}_{scale}"
                permanent_path = os.path.join(IMAGES_DIR, f"{base_filename}.png")

                # Check for duplicates and increment suffix
                if os.path.exists(permanent_path):
                    counter = 1
                    while True:
                        new_path = os.path.join(IMAGES_DIR, f"{base_filename}_{counter}.png")
                        if not os.path.exists(new_path):
                            permanent_path = new_path
                            break
                        counter += 1

                with open(permanent_path, "wb") as f:
                    f.write(img_bytes)

                # Get image info
                w, h = img.size
                size_kb = len(img_bytes) / 1024
                console.print(f"[green]OK[/green] Image downloaded: {w}x{h} ({size_kb:.1f}KB)")
                console.print(f"[dim]Saved to: {permanent_path}[/dim]")
                return permanent_path
            except Exception as verify_error:
                console.print(f"[yellow]Warning: Downloaded data is not a valid image: {verify_error}[/yellow]")
                return None

        except Exception as e:
            console.print(f"[yellow]Warning: Error downloading image: {e}[/yellow]")
            return None

    def save_pdf(self, row: int, address: str, scale: str = "1200") -> Optional[str]:
        """
        상단 상세 정보 표부터 하단의 법령정보까지 한 페이지에 담은 전체 결과를 PDF로 저장하는 로직.
        메인 화면에서 [인쇄] 버튼을 누르고 -> [전체 인쇄] 레이어를 연 뒤 -> 
        인쇄 전용 깔끔한 팝업창('luLandDetPrintPop.jsp')이 뜨면 이를 감지하여 A4 PDF로 변환 및 저장합니다. 
        (단, 웹사이트 한계상 이 메인 인쇄창은 1/1200 단일 축척 상태로 출력됩니다)
        
        Args:
            row: 엑셀 행 번호
            address: 주소 문자열 (파일 이름용)
            scale: 지도 축척 매개변수
            
        Returns:
            저장된 PDF 파일 경로 또는 실패 시 None
        """
        try:
            # Check if running in headless mode, as page.pdf only supports headless
            if not self.headless:
                # Some versions/browsers might support it, but generally it's a headless feature in Playwright
                # We'll try anyway but catch error specifically if it complains
                pass

            # 1. Click Print button to open layer
            self.log("[dim]Clicking print button...[/dim]")
            print_btn = self.page.query_selector(SELECTORS["PRINT_BTN"])
            if not print_btn:
                self.log("[yellow]Print button not found[/yellow]")
                return None
            
            print_btn.click()
            time.sleep(1) # Wait for layer animation
            
            # 2. Click Popup button in layer
            self.log("[dim]Clicking print popup link...[/dim]")
            popup_btn = self.page.query_selector(SELECTORS["PRINT_POPUP_BTN"])
            if not popup_btn:
                self.log("[yellow]Print popup button not found in layer[/yellow]")
                return None
                
            # Prepare to catch new page
            with self.context.expect_page() as page_catcher:
                popup_btn.click()
                
            print_page = page_catcher.value
            if not print_page:
                self.log("[red]Failed to catch print popup page[/red]")
                return None
                
            self.log("[cyan]Print popup opened, waiting for load...[/cyan]")
            print_page.wait_for_load_state("domcontentloaded")
            # Wait a bit more for map tiles to render
            time.sleep(3) 
            
            # 3. Save as PDF
            # Sanitize filename
            safe_filename = address.replace(" ", "_")
            safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ("_", "-"))
            
            # Filename format: {row}_{address}_{scale}
            base_filename = f"{row}_{safe_filename}_{scale}"
            pdf_path = os.path.join(PDF_DIR, f"{base_filename}.pdf")
            
            # Check for duplicates and increment suffix
            if os.path.exists(pdf_path):
                counter = 1
                while True:
                    new_pdf_path = os.path.join(PDF_DIR, f"{base_filename}_{counter}.pdf")
                    if not os.path.exists(new_pdf_path):
                        pdf_path = new_pdf_path
                        break
                    counter += 1
            
            self.log(f"[cyan]Saving PDF to {pdf_path}...[/cyan]")
            print_page.pdf(path=pdf_path, format="A4", print_background=True)
            self.log(f"[green]OK[/green] PDF Saved: {pdf_path}")
            
            print_page.close()
            return pdf_path
            
        except Exception as e:
            self.log(f"[red]Error saving PDF: {e}[/red]")
            return None

    def scrape_address(self, address: str, row: int, pnu: str = None, scale: str = "1200", 
                       debug_mode: bool = False, step_event = None) -> Optional[Dict[str, str]]:
        """
        Complete scraping process for one address.

        Args:
            address: Address to search
            row: Row number for image naming
            pnu: PNU code (optional, needed for popup image)
            scale: Map scale (optional, default "1200")
            debug_mode: Whether to run in debug mode
            step_event: Event to wait for
        """
        success, msg = self.search_address(address, pnu=pnu, scale=scale)
        if not success:
            self.log(f"[yellow]Skipping scrape due to search failure: {msg}[/yellow]")
            return None

        # Extract data
        data = self.extract_data()

        # Download image
        """
        이전 코드
        image_path = None
        if scale == "1200":
            # 기본 축척(1/1200)만 일반 다운로드
            image_path = self.download_image(row, address)
        elif pnu:
            # 나머지 축척은 모두 팝업창 다운로드 (PNU 필요)
            image_path = self.download_image_from_popup(row, address, pnu, scale, debug_mode, step_event)
        else:
            # PNU가 없으면 일반 다운로드로 fallback
            image_path = self.download_image(row, address)
        """
        image_path = self.download_image(row, address, scale=scale)
            
        if image_path:
            data["image_path"] = image_path

        return data

    def close(self):
        """Close the browser and cleanup."""
        if self.popup_page:
            self.popup_page.close()
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
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
