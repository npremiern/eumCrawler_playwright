"""Configuration settings for the crawler."""

# Target website
BASE_URL = "https://www.eum.go.kr/"

# Excel column mapping
EXCEL_COLUMNS = {
    "ADDRESS_INPUT": "B",      # Input: Search address
    "PRESENT_ADDR": "C",       # Output: Address
    "PRESENT_CLASS": "D",      # Output: Classification
    "PRESENT_AREA": "E",       # Output: Area
    "JIGA": "F",               # Output: Land price
    "PRESENT_MARK1": "G",      # Output: Mark 1
    "PRESENT_MARK2": "H",      # Output: Mark 2
    "PRESENT_MARK3": "I",      # Output: Mark 3
    "IMAGE": "J",              # Output: Image
}

# CSS Selectors
SELECTORS = {
    "SEARCH_INPUT": "#recent > input",
    "PRESENT_ADDR": "#present_addr",
    "PRESENT_CLASS": "#present_class",
    "PRESENT_AREA": "#present_area",
    "JIGA": "#jiga",
    "PRESENT_MARK1": "#present_mark1",
    "PRESENT_MARK2": "#present_mark2",
    "PRESENT_MARK3": "#present_mark3",
    "IMAGE": "#appoint > div:nth-child(4) > table > tbody > tr:nth-child(1) > td.m_pd0.vtop > div > div > img",
}

# Timing settings
DEFAULT_WAIT_TIME = 5  # seconds (increased for dynamic content loading)
PAGE_LOAD_TIMEOUT = 30000  # milliseconds
MAX_RETRIES = 3

# Image settings
IMAGE_WIDTH = 300  # pixels
TEMP_IMAGE_DIR = "temp_images"
IMAGES_DIR = "images"  # Permanent image storage

# Default values
DEFAULT_START_ROW = 2
