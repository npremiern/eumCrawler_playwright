# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**eumcrawl** is a CLI application that automatically crawls real estate information from the Korean government website (eum.go.kr). It reads addresses from an Excel file, scrapes property data including images, and writes the results back to the Excel file.

Target website: https://www.eum.go.kr/ (국토교통부 부동산공시가격 알리미)

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Mac/Linux)
source venv/bin/activate

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required)
playwright install chromium
```

### Running the Application
```bash
# Basic usage
python crawler.py --file example_data.xlsx

# With options
python crawler.py --file data.xlsx --start-row 3 --verbose --no-headless

# Run with specific wait time
python crawler.py --file data.xlsx --wait 5
```

### Testing
```bash
# Create example Excel file first
python create_example_data.py

# Test with example data
python crawler.py --file example_data.xlsx --verbose --no-headless
```

### Building Executable
```bash
# Build Windows executable
python build.py

# Or use PyInstaller directly
pyinstaller crawler.spec

# Output will be in: dist/crawler.exe
```

## Code Architecture

### Core Components

**crawler.py** - Main CLI application
- Entry point using Click framework
- Orchestrates Excel reading, web scraping, and data writing
- Handles command-line arguments and user feedback via Rich console
- Manages the complete workflow: setup → process rows → cleanup

**scraper.py** - Web scraping logic
- Uses Playwright (Chromium) for browser automation
- Implements `RealEstateScraper` class with context manager support
- Handles: page navigation, address search, data extraction, image downloading
- Includes retry logic for network failures (max 3 attempts)
- Downloads images to `temp_images/` directory

**excel_handler.py** - Excel file operations
- Uses openpyxl for reading/writing Office 365 format (.xlsx)
- Implements `ExcelHandler` class with context manager support
- Reads addresses from column B
- Writes extracted data to columns C-I
- Inserts and resizes images in column J (300px width)

**config.py** - Configuration and constants
- Excel column mappings (B=input address, C-J=output fields)
- CSS selectors for web scraping
- Timing settings (default wait: 3s, timeout: 30s)
- Image settings (width: 300px, temp directory path)

### Data Flow

1. **Input**: Excel file with addresses in column B (starting row 2)
2. **Process**: For each row:
   - Read address from column B
   - Navigate to eum.go.kr
   - Search address via selector `#recent > input`
   - Wait for results page to load
   - Extract data from selectors (#present_addr, #present_class, etc.)
   - Download image from specific table cell selector
   - Write data to columns C-I and insert image in column J
   - Save Excel file (prevents data loss on interruption)
3. **Output**: Excel file with populated data and images

### Excel Column Structure

| Column | Field | Type | Description |
|--------|-------|------|-------------|
| A | ID | Input | Optional identifier |
| B | Address | Input | Search address (required) |
| C | present_addr | Output | Official address |
| D | present_class | Output | Property classification |
| E | present_area | Output | Area (면적) |
| F | jiga | Output | Land price (지가) |
| G | present_mark1 | Output | Mark 1 (표시1) |
| H | present_mark2 | Output | Mark 2 (표시2) |
| I | present_mark3 | Output | Mark 3 (표시3) |
| J | Image | Output | Property image |

### Scraping Selectors

All selectors are defined in `config.py`:
- Search input: `#recent > input`
- Result fields: `#present_addr`, `#present_class`, `#present_area`, `#jiga`, etc.
- Image: `#appoint > div:nth-child(4) > table > tbody > tr:nth-child(1) > td.m_pd0.vtop > div > div > img`

## Important Implementation Details

### Browser Automation
- Uses Playwright's Chromium browser in headless mode by default
- Page load timeout: 30 seconds
- Default wait time between actions: 3 seconds (configurable via `--wait`)
- Searches by filling input and pressing Enter key (not clicking search button)

### Error Handling Strategy
- **Missing Excel file**: Exit with error message
- **Empty address cell**: Stop processing (end of data)
- **Network errors**: Retry up to 3 times with wait intervals
- **No search results**: Log warning, skip row, continue to next
- **Missing page elements**: Log warning, write empty value, continue
- **Image download failure**: Log warning, continue without image

### Data Persistence
- Excel file is saved after EACH row is processed
- This prevents data loss if process is interrupted
- Temporary images are stored in `temp_images/` directory
- Images are resized (300px width) before Excel insertion
- Cleanup: temp_images/ directory is deleted on completion

### Performance Characteristics
- Average processing time: 5-10 seconds per address
- 100 addresses: approximately 10-15 minutes
- Network-dependent (wait times account for page load variability)

## Modifying the Code

### Changing Target Website Fields
1. Update CSS selectors in `config.py` SELECTORS dictionary
2. Update column mappings in `config.py` EXCEL_COLUMNS dictionary
3. Modify extraction logic in `scraper.py` extract_data() if needed
4. Update Excel writing in `excel_handler.py` write_data() if needed

### Adding New CLI Options
1. Add Click option decorator in `crawler.py` main() function
2. Pass new parameter through to ExcelHandler or RealEstateScraper
3. Update README.md documentation

### Adjusting Timing/Retry Logic
- Modify `DEFAULT_WAIT_TIME` in config.py for global wait time
- Modify `MAX_RETRIES` in config.py for retry attempts
- Adjust `PAGE_LOAD_TIMEOUT` for slower connections

## Dependencies

Critical dependencies:
- **playwright**: Browser automation (requires separate browser installation)
- **openpyxl**: Excel file handling (Office 365 format only)
- **click**: CLI framework
- **rich**: Terminal output formatting
- **pillow**: Image processing
- **requests**: Image downloading

## Platform Notes

### Windows EXE Build
- Uses PyInstaller to create standalone executable
- Chromium browser (~200MB) requires separate installation
- First run may trigger antivirus false positives (common with PyInstaller)
- Users must run `playwright install chromium` after first execution

### Cross-Platform Compatibility
- Code runs on Windows, macOS, and Linux
- PyInstaller spec file (crawler.spec) is configured for single-file output
- Browser installation is platform-specific (handled by Playwright)

## Common Issues

**"Playwright browser not found"**
- Run: `playwright install chromium`
- Build script attempts automatic installation

**Selectors not working**
- Website structure may have changed
- Update selectors in config.py
- Use `--no-headless` to debug visually

**Excel file locked**
- Close Excel file before running crawler
- File must not be open by another process

**Slow performance**
- Increase `--wait` time for slower networks
- Website response time varies by traffic

**Image insertion fails**
- Check Pillow installation
- Verify image URL is accessible
- Check disk space for temp_images/
