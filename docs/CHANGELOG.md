# Changelog

## [1.7.0] - 2026-03-16

### Added
- **UI 프레임워크 전환 (`ttkbootstrap`)**: 기존 `sv_ttk`에서 더 다채롭고 모던한 `ttkbootstrap`으로 전면 교체.
- **다이나믹 버튼 스타일**: 시작(Green), 중지(Red), 저장(Blue), 초기화(Orange) 등 작업 성격에 맞는 색상 적용으로 시인성 개선.
- **네트워크 상태 모니터링**: 대상 사이트(`eum.go.kr`)의 응답 속도를 실시간으로 체크하여 우측 하단에 상태 표시기(색상 점 및 ms) 추가.
- **지능형 재시도 시스템**: 네트워크 응답이 느리거나 불안정할 경우 설정된 재시도 횟수를 자동으로 늘려 성공률 극대화.
- **재시도 횟수 설정 추가**: 상세 설정 팝업에서 '실패 시 재시도 횟수'를 직접 조절 가능(기본 2회).
- **테마 기억 기능**: 사용자가 선택한 라이트/다크 모드를 종료 후에도 기억하여 다음 실행 시 자동 복원.

### Changed
- **컬럼명 축소**: 엑셀 전용 '통합규제' 컬럼명을 더 명확한 '통합'으로 변경.
- **재시도 간격 최적화**: 재시도 횟수가 늘어날수록 대기 시간도 점진적으로 증가(Backoff)하도록 개선.
- **UI 위젯 보정**: 테마 변경 시 버튼이 짤려 보이던 현상 수정 및 텍스트 맞춤.

### Technical Details
- `crawler_gui.py`: `ttkbootstrap.Window` 적용, `_check_network_response` 및 `Canvas` 기반 인디케이터 구현.
- `crawler.py`: `max_retries` 파라미터화 및 동적 재시도 루프 로직 고도화.
- `config.py`: `VERSION` 1.7 업데이트 및 `TEMPLATE_HEADERS` 컬럼명 수정.


## [1.6.0] - 2026-03-16

### Added
- **시작 시 브라우저 자동 실행**: 프로그램 구동 즉시 Playwright 브라우저를 백그라운드에서 실행하고 기본 URL(토지이음)에 접속. 시작 버튼을 누르면 바로 크롤링 가능.
- **완료 후 초기화 버튼**: 크롤링 완료 시 '시작' 버튼이 '초기화'로 전환됨. 클릭 시 로드된 파일, 그리드, 통계, 로그를 모두 초기화.
- **엑셀 로드 시 PNU 자동 표시**: 엑셀 파일 로드 시 기존에 저장된 PNU 값을 그리드에 즉시 표시.
- **PNU 자동 백그라운드 조회**: 엑셀 파일 로드 후 PNU가 없는 행을 백그라운드에서 자동으로 조회하여 그리드 및 엑셀 파일 업데이트.
- **크롤링 시 PNU 재사용**: 1단계 검증 시 엑셀에 이미 PNU가 있으면 Ajax 조회 없이 즉시 통과(속도 대폭 향상).
- **작업 목록 복사 기능**: 그리드 항목 우클릭 컨텍스트 메뉴 및 Ctrl+C 단축키로 데이터 복사 지원.
- **통합규제 컬럼 추가**: 엑셀 저장 시 지역지구1, 지역지구2, 토지이용규제를 결합한 '통합규제' 컬럼 자동 생성.
- **Windows 트레이 아이콘 교체**: 기본 파이썬 아이콘 대신 프로그램 고유 아이콘으로 표시(`AppUserModelID` 설정).

### Changed
- **첫 번째 컬럼명 변경**: 작업 목록 및 엑셀 양식의 첫 번째 컬럼명을 `ID` → `NO`로 변경.
- **기본 테마**: 기본 테마를 다크에서 라이트(흰 화면)로 변경.
- **엑셀 ID 보존**: 크롤링 시 새 ID를 채번하지 않고 엑셀 파일에 있는 기존 ID 값을 유지. 비어있으면 빈 값으로 처리.
- **에러 메시지 간소화**: 타임아웃 등 긴 에러 메시지를 한 줄로 간소화하여 엑셀 상세내용에 저장.
- **단일 스레드 브라우저 구조**: Playwright 스레드 충돌 방지를 위해 브라우저 초기화부터 크롤링까지 동일 스레드에서 처리하는 영구 대기열 구조로 변경.

### Technical Details
- `crawler_gui.py`: 영구 루프 브라우저 스레드, `pnu_fetch_queue`, `fetch_pnu_cancel` 이벤트 추가
- `crawler.py`: `scraper_instance` 파라미터 추가로 기존 브라우저 세션 재사용
- `excel_handler.py`: `read_pnu()` 메서드 추가
- `config.py`: `PRESENT_MARK_COMBINED` 컬럼, `TEMPLATE_HEADERS`에 `통합규제` 추가
- `scraper.py`: 타임아웃 에러 메시지 첫 줄 추출 및 직관적 메시지로 변환

## [1.5.0] - 2026-03-10

### Fixed
- **Build Tools**: Fixed `pkg_resources` dependencies and absolute path execution bugs allowing GUI to build successfully right from the root directory.

## [1.4.0] - 2026-01-29

### Fixed
- **File Naming System**: Completely overhauled file naming to use sequential IDs
  - All output files (PDF, images, Excel ID column) now use a consistent 1-based sequential ID
  - Sequential ID starts from 1 regardless of the Excel start row setting
  - Duplicate file handling: Uses numeric suffixes (e.g., `1_address.pdf`, `1_address_1.pdf`)
  - Image files: Format changed to `{ID}_{address}_{scale}.png` (e.g., `1_서울특별시_1200.png`)
  - PDF files: Format changed to `{ID}_{address}.pdf` (e.g., `1_서울특별시.pdf`)

- **Data Duplication Issue**: Fixed duplicate data appearing for different addresses
  - Added forced page refresh before each search to prevent stale data
  - Ensures each search starts from a clean state

- **Multiple Search Results**: Fixed timeout errors when multiple addresses appear
  - Implemented automatic selection of the first dropdown result
  - Updated selector to `#recent > div.recent_list.addrDiv > div > ul > li:nth-child(1) > a`

- **Excel File Corruption**: Resolved file corruption issues after crawling completion
  - Changed from per-row saving to batch saving (every 5 rows)
  - Added filesystem delay before final save
  - Significantly improved file stability and reduced I/O operations

### Changed
- **Progress Display**: Updated progress text to show sequential ID instead of Excel row number
  - Format: "1번 처리 중", "2번 완료" instead of row numbers

- **Excel Error Handling**: Enhanced error feedback when Excel file fails to load
  - Displays specific error message with instructions to download new template
  - Automatically clears the selected file path on error

### Added
- **UI Reset on File Selection**: Implemented comprehensive state reset when new file is selected
  - Clears work list table, statistics, progress bar, logs
  - Resets all internal events and button states
  - Settings (start row, headless mode, etc.) are preserved

- **Window Size Persistence**: Added window geometry saving
  - Window size and position are saved to `gui_config.json` on exit
  - Automatically restored on next application launch
  - Falls back to default 800x900 if no saved settings exist

### Technical Details
- Modified `scraper.py` to handle dropdown selection with proper selector
- Updated `crawler.py` batch save logic with `rows_since_save` counter
- Enhanced `crawler_gui.py` with `reset_ui()` method and geometry persistence
- Added `load_window_geometry()` and `save_window_geometry()` methods

## [1.3.0] - 2026-01-28

## [1.2.0] - 2025-12-18
### Added
- **PDF Saving**:
  - Automatically saves the print view of the search result as a PDF file.
  - PDF files are stored in the new `pdfs/` directory.
- **Robust Image Downloading**:
  - Improved image downloading logic to handle relative URLs and session-based authentication.
  - Added strong error handling and logging for download failures (e.g., fetch errors).
- **Absolute Path Management**:
  - Configured `images`, `pdfs`, `temp_images` directories to be created using absolute paths based on the execution environment.
  - Ensures correct folder creation whether running as a Python script or a PyInstaller EXE.
- **Search Error Details**:
  - Detailed error reasons (timeout, network error, etc.) are now logged and saved to Excel when address search fails.

### Changed
- **Image Filenames**: 
  - Image filenames now include the scale information (e.g., `Address_1200.png` or `Address_3000.png`).
- **Data Saving**:
  - Re-enabled automatic Excel saving after every row to prevent data loss in case of interruption.
  - Added visual error logs if saving fails (e.g., if the file is open).
- **Data Extraction**:
  - Improved data extraction efficiency by excluding button elements (`PRINT_BTN`) from the text extraction loop.
- **Version**: Updated application version to **v1.2**.

## [1.1.0] - 2025-12-08 (Evening Session)

### Fixed
- **GUI Data Display Issue**:
  - Fixed critical bug where scraped data was not appearing in the GUI "Work List".
  - Implemented thread-safe GUI updates using `root.after()` for all callbacks (`log`, `update_progress`, `update_data`).
  - Added `data_callback` and `save_request_event` parameters to `run_crawler` function.
- **Robust Web Selectors**:
  - Changed all data field selectors from ID-based to XPath-based for better reliability.
  - Updated selectors: `PRESENT_ADDR`, `PRESENT_CLASS`, `PRESENT_AREA`, `JIGA` now use `xpath=//th[contains(text(), '...')]/following-sibling::td`.
  - Changed zone selectors back to ID-based (`#present_mark1`, `#present_mark2`, `#present_mark3`) for stability.
- **Browser Context Error**:
  - Fixed "Please use browser.new_context()" error in image download.
  - Added explicit browser context creation in `scraper.py`.
  - Updated popup page creation to use `self.context.new_page()`.

### Changed
- **Column Names**:
  - Renamed "ë¶„ë¥˜" to "ì§€ëª©" in GUI and Excel output.
  - Added "ì§€ê°€ì—°ë�„" column to separate year from price data.
- **Data Processing**:
  - **ì§€ëª© (Land Category)**: Automatically removes "?" characters and trims whitespace.
  - **ì§€ê°€ (Land Price)**: Now parsed to extract year separately.
    - Example: `67,300,000ì›� (2025/01)` â†’ `ì§€ê°€: 67,300,000ì›�`, `ì§€ê°€ì—°ë�„: 2025/01`
  - **ì�´ë¯¸ì§€ì—¬ë¶€ (Image Status)**: Changed from "O/X" to "Y/N" format.
- **Image Handling**:
  - Removed image resizing logic - now saves **original size images**.
  - Images are saved without any resize/compression in both temp and permanent folders.
  - Excel row height automatically adjusts to image height.
- **GUI Layout Optimization**:
  - Reduced window width from 1200px to 800px (2/3 size).
  - Merged "ì§„í–‰ ìƒ�í™©" and "í†µê³„" into a single compact horizontal line.
  - Shortened statistics format: "ê²½ê³¼ ì‹œê°„: 0ì´ˆ" â†’ "ì‹œê°„: 0s".
  - Progress bar reduced from 400px to 150px width.
  - Font size reduced from 10 to 9 for statistics.

### Added
- **Horizontal Scrollbar**: Added to Treeview for better handling of wide data.
- **ì§€ê°€ì—°ë�„ Column**: New column in both GUI and Excel to store land price year.
- **Debug Logging**: Extensive debug logs added to track data extraction and GUI updates.
- **Auto Save on Completion**: Excel file automatically saves when crawling completes or stops.

### Technical Details
- Updated `EXCEL_COLUMNS` mapping: shifted all columns after JIGA by one position to accommodate JIGA_YEAR.
- Added regex parsing in `extract_data` to split JIGA into price and year.
- Enhanced `_update_data_impl` with detailed logging for troubleshooting.
- GUI "ì €ìž¥" (Save) button now enables during crawling and disables after completion.

## [1.0.0] - 2025-12-08 (Initial Session)

### Added
- **Download Template Feature**:
  - Added "ì–‘ì‹� ë‹¤ìš´ë°›ê¸°" button to GUI.
  - Implemented `create_template` in `ExcelHandler` to generate a standard Excel template.
  - Defined `TEMPLATE_HEADERS` in `config.py` with columns: ID, Address, Result, Details, PNU, Class, Area, Jiga, Zone1, Zone2, Regulation, ImageStatus.
- **Manual Save Feature**:
  - Added "ì €ìž¥" (Save) button to GUI.
  - Implemented manual save logic: GUI sets a flag, and the crawler thread saves the file at the next convenient point.
- **In-Memory Data Handling**:
  - Modified `run_crawler` to stop saving to Excel automatically after every row.
  - Implemented `data_callback` to update the GUI "Work List" in real-time without disk I/O.
  - The Excel file is now only saved when the "Save" button is clicked or when the crawling process finishes.
- **Debug Mode (Step-by-step Execution)**:
  - Added a "Debug Mode" checkbox in the GUI settings.
  - Implemented step-by-step execution control using a "Next" button.
  - Added breakpoints: after browser start, after validation phase, before each scraping row, and before popup image download.
- **PNU Code Extraction & Output**:
  - Extracted PNU code from `mpSearchAddrAjaxXml.jsp` response during validation.
  - Added "PNU" column to the GUI results table.
  - Added "PNU" column to the Excel output file.
- **Conditional Image Downloading**:
  - Implemented logic to download images from a popup URL (`luLandPop.jsp`) if the selected map scale is not "1/1200".
  - Added `download_image_from_popup` method to `RealEstateScraper`.
- **Map Scale Selection**:
  - Added a dropdown in GUI to select "Cadastral Map Scale" (e.g., 1/1200, 1/3000).

### Changed
- **GUI Work List**:
  - Updated Treeview columns to display all scraped fields: ID, Address, Result, Details, PNU, Class, Area, Jiga, Zone1, Zone2, Regulation, ImageStatus.
  - Updated `update_progress` and added `update_data` to populate these columns.
- **Crawler Logic**:
  - `run_crawler` now accepts `data_callback` and `save_request_event` for better GUI integration and control.
  - Removed periodic saving in validation phase and per-row saving in scraping phase to improve performance and reduce file corruption risks.
- **Crawling Process**:
  - Refactored into a **Two-Phase Process**:
    1.  **Validation Phase**: Batch validates all addresses using Ajax, extracts PNU, and filters invalid rows.
    2.  **Scraping Phase**: Scrapes detailed data and images only for validated addresses.
- **Image Download Mechanism**:
  - Refactored `download_image_from_popup` to **reuse a single separate browser tab** for downloading images. This avoids navigating away from the main search page and improves performance compared to opening/closing tabs for every request.
- **Logging**:
  - Centralized logging: Internal scraper logs (including Ajax errors) are now routed to the GUI log window.
  - Enhanced Ajax response logging: Logs raw XML/JSON responses in verbose mode for debugging.
- **Excel Handling**:
  - Optimized save frequency: During validation, data is saved every 50 rows instead of every row to prevent file corruption and improve speed.
  - Added explicit error logging for file open failures (e.g., file locked).

### Fixed
- **Excel Column Mapping**:
  - Updated `EXCEL_COLUMNS` in `config.py` to match the new requested layout.
- **Ajax Response Parsing**:
  - Fixed XML parsing errors caused by JSON-wrapped XML responses from the server.
  - Implemented automatic encoding detection (EUC-KR/UTF-8) for Korean characters in server responses.
- **Excel File Corruption**:
  - Resolved issues where the Excel file became corrupted due to frequent saving or improper closure.
- **Code Errors**:
  - Fixed `IndentationError` and `SyntaxError` in `scraper.py` and `excel_handler.py`.
  - Fixed `NameError` for `IMAGE_WIDTH` by importing it correctly.

 
 # #   [ 1 . 3 . 0 ]   -   2 0 2 6 - 0 1 - 2 9 
 
 # # #   C h a n g e d 
 
 -   * * G U I   L a y o u t   O v e r h a u l * * : 
 
     -   R e d e s i g n e d   s e t t i n g   m a n a g e m e n t :   C r e a t e d   a   c l e a n e r   i n t e r f a c e   b y   h i d i n g   a d v a n c e d   s e t t i n g s   ( W a i t   T i m e ,   V e r b o s e ,   D e b u g )   i n   a   " D e t a i l e d   S e t t i n g s "   p o p u p . 
 
     -   S i m p l i f i e d   M a i n   C o n t r o l   A r e a :   N o w   p r o m i n e n t l y   f e a t u r e s   ' P D F   D o w n l o a d '   a n d   ' M a p   S c a l e '   s e t t i n g s   d i r e c t l y   o n   t h e   m a i n   s c r e e n . 
 
     -   O p t i m i z e d   B u t t o n   L a y o u t :   M o v e d   S t a r t / S t o p / S a v e   b u t t o n s   t o   a   s i n g l e   h o r i z o n t a l   r o w   w i t h   r e d u c e d   w i d t h   f o r   a   m o r e   c o m p a c t   a n d   b a l a n c e d   l o o k . 
 
     -   E n h a n c e d   V i s u a l s :   U p d a t e d   t h e   ' D e t a i l e d   S e t t i n g s '   b u t t o n   t o   a   c l e a n   g e a r   i c o n   ( ? ÂÒ)   a n d   r e f i n e d   e l e m e n t   s p a c i n g . 
 
 -   * * L o g   M a n a g e m e n t * * : 
 
     -   I m p r o v e d   U I   S p a c e :   T h e   l o g   a r e a   i s   n o w   h i d d e n   b y   d e f a u l t   t o   k e e p   t h e   i n t e r f a c e   c l e a n . 
 
     -   A d d e d   a   " S h o w   L o g s "   t o g g l e   b u t t o n   t o   e x p a n d / c o l l a p s e   t h e   l o g   v i e w e r   a s   n e e d e d . 
 
 -   * * I D   D i s p l a y * * : 
 
     -   C h a n g e d   t h e   " I D "   c o l u m n   i n   t h e   r e s u l t   t a b l e   t o   a l w a y s   d i s p l a y   a   s e q u e n t i a l   n u m b e r   s t a r t i n g   f r o m   1 ,   i n d e p e n d e n t   o f   t h e   a c t u a l   r o w   n u m b e r   i n   t h e   E x c e l   f i l e . 
 
 -   * * S e a r c h   L o g i c * * : 
 
     -   U p d a t e d   a d d r e s s   v a l i d a t i o n   l o g i c :   I f   m u l t i p l e   s e a r c h   r e s u l t s   a r e   f o u n d   ( e . g . ,   d u p l i c a t e d   a d d r e s s e s ) ,   t h e   p r o g r a m   n o w   a u t o m a t i c a l l y   s e l e c t s   t h e   f i r s t   r e s u l t   i n s t e a d   o f   f a i l i n g   v a l i d a t i o n . 
 
 -   * * V e r s i o n * * :   U p d a t e d   a p p l i c a t i o n   v e r s i o n   t o   * * v 1 . 3 * * . 
 
 