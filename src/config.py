"""Configuration settings for the crawler."""

import sys
import os
from pathlib import Path

# Application Version
VERSION = "1.7"

# Target website
BASE_URL = "https://www.eum.go.kr/"

# Excel column mapping
# Maps data fields to Excel column letters (A, B, C, etc.)
EXCEL_COLUMNS = {
    "ID": "A",                 # Sequence number (auto-incremented)
    "ADDRESS_INPUT": "B",      # Input: User-provided address to search
    "RESULT": "C",             # Output: Success/Failure status (성공/실패/검증실패)
    "DETAILS": "D",            # Output: Failure reason or details
    "PNU": "E",                # Output: Parcel Number (PNU code)
    "PRESENT_CLASS": "F",      # Output: Land classification (지목)
    "PRESENT_AREA": "G",       # Output: Land area (면적)
    "JIGA": "H",               # Output: Individual land price (개별공시지가)
    "JIGA_YEAR": "I",          # Output: Land price reference year (지가연도)
    "PRESENT_MARK1": "J",      # Output: Zoning designation 1 (지역지구1)
    "PRESENT_MARK2": "K",      # Output: Zoning designation 2 (지역지구2)
    "PRESENT_MARK3": "L",      # Output: Land use regulation (토지이용규제)
    "PRESENT_MARK_COMBINED": "M", # Output: Combined zoning and regulations (통합규제)
    "IMAGE_STATUS": "N",       # Output: Image availability (Y/N)
    "IMAGE": "O",              # Output: Actual embedded image (optional)
}

# Template headers for creating new Excel files
TEMPLATE_HEADERS = [
    "NO", "주소(입력)", "결과", "상세내용", "PNU", "지목", "면적", "지가", "지가연도",
    "지역지구1", "지역지구2", "토지이용규제", "통합", "이미지여부"
]

# CSS Selectors for web scraping
# These selectors target specific elements on the eum.go.kr website
SELECTORS = {
    "SEARCH_INPUT": "#recent > input",                                              # Address search input field
    "PRESENT_ADDR": "xpath=//th[contains(text(), '소재지')]/following-sibling::td",  # Location (소재지)
    "PRESENT_CLASS": "xpath=//th[contains(text(), '지목')]/following-sibling::td",   # Land classification (지목)
    "PRESENT_AREA": "xpath=//th[contains(text(), '면적')]/following-sibling::td",    # Area (면적)
    "JIGA": "xpath=//th[contains(text(), '개별공시지가')]/following-sibling::td",      # Land price (개별공시지가)
    "PRESENT_MARK1": "#present_mark1",                                              # Zoning 1 (지역지구1)
    "PRESENT_MARK2": "#present_mark2",                                              # Zoning 2 (지역지구2)
    "PRESENT_MARK3": "#present_mark3",                                              # Land use regulation (토지이용규제)
    "IMAGE": "#appoint > div:nth-child(4) > table > tbody > tr:nth-child(1) > td.m_pd0.vtop > div > div > img",  # Map image
    "PRINT_BTN": "#appoint > div.btn_area > div > a",                                               # Print button on result page
    "PRINT_POPUP_BTN": "#appoint > div.btn_area > div > div > div > div > div.layer_body > div > p.al_c.mt20 > span > a",  # Print button in layer
}

# Timing settings
DEFAULT_WAIT_TIME = 5      # Default wait time after page loads (seconds)
PAGE_LOAD_TIMEOUT = 30000  # Maximum time to wait for page load (milliseconds)
MAX_RETRIES = 3           # Maximum number of retry attempts on failure

# Determine base directory based on execution environment
if getattr(sys, 'frozen', False):
    # If running as PyInstaller exe, use the directory of the executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # If running as script, use the project root (parent of src)
    # config.py is in src/, so go up one level
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Image settings
IMAGE_WIDTH = 300          # Target width for images in Excel (pixels)

# Setup absolute paths for directories
# This ensures they are created in the correct location regardless of CWD
TEMP_IMAGE_DIR = os.path.join(BASE_DIR, "temp_images")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
PDF_DIR = os.path.join(BASE_DIR, "pdfs")

# Ensure directories exist
for directory in [TEMP_IMAGE_DIR, IMAGES_DIR, PDF_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# Default values for crawler execution
DEFAULT_START_ROW = 2      # Default starting row in Excel (row 1 is header)

