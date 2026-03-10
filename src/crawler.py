"""Main CLI application for real estate information crawler."""

import os
import sys
import time
import shutil
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from config import DEFAULT_START_ROW, DEFAULT_WAIT_TIME, TEMP_IMAGE_DIR, VERSION
from excel_handler import ExcelHandler
from scraper import RealEstateScraper
from console_helper import console


def setup_playwright(log_callback=None):
    """Check and setup Playwright browsers."""
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            console.print(message)
    
    try:
        # Set up portable browser path if running as exe
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            # Running as exe - set browser path to local folder
            exe_dir = Path(os.path.dirname(sys.executable))
            browsers_dir = exe_dir / 'browsers'

            # Set environment variable for Playwright to use local browsers
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(browsers_dir)

            # Auto-extract chromium-win64.zip if it exists and browser is not installed
            chromium_zip = exe_dir / 'chromium-win64.zip'
            chromium_path = browsers_dir / 'chromium-1194'

            if chromium_zip.exists() and not chromium_path.exists():
                log("[cyan]Extracting Chromium browser from package...[/cyan]")
                log("[cyan]패키지에서 Chromium 브라우저 압축 해제 중...[/cyan]")

                try:
                    import zipfile
                    browsers_dir.mkdir(exist_ok=True)

                    with zipfile.ZipFile(chromium_zip, 'r') as zip_ref:
                        zip_ref.extractall(browsers_dir)

                    # Rename extracted folder to expected name
                    extracted_folders = [
                        browsers_dir / 'chrome-win',
                        browsers_dir / 'chromium-win64'
                    ]

                    for folder in extracted_folders:
                        if folder.exists():
                            folder.rename(chromium_path)
                            log("[green]OK[/green] Browser extracted successfully!")
                            log("[green]OK[/green] 브라우저 압축 해제 완료!")
                            break
                except Exception as extract_error:
                    log(f"[yellow]Warning: Failed to extract browser: {extract_error}[/yellow]")

        # Try to import and use playwright
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                # Try to launch browser to check if it's installed
                browser = p.chromium.launch(headless=True)
                browser.close()
            except Exception as e:
                # Browser not found, install it
                log("\n" + "="*60)
                log("[bold yellow]첫 실행 설정 (First-time Setup)[/bold yellow]")
                log("="*60)
                log("[cyan]Chromium 브라우저를 다운로드합니다...[/cyan]")
                log("[cyan]Downloading Chromium browser...[/cyan]")
                log("[dim]크기: 약 200MB | Size: ~200MB[/dim]")
                log("[dim]소요 시간: 3-5분 | Time: 3-5 minutes[/dim]")
                log("="*60 + "\n")

                # Check if running as PyInstaller bundle
                is_frozen = getattr(sys, 'frozen', False)

                if is_frozen:
                    # Running as executable - find playwright driver in bundled files
                    try:
                        import subprocess

                        # Try to find playwright driver in the bundled executable
                        if hasattr(sys, '_MEIPASS'):
                            # PyInstaller sets _MEIPASS to temp directory where files are extracted
                            driver_path = Path(sys._MEIPASS) / 'playwright' / 'driver'

                            # Look for playwright CLI executable
                            driver_exe = None
                            if sys.platform == 'win32':
                                # Windows: look for playwright.cmd or node.exe
                                possible_paths = [
                                    driver_path / 'playwright.cmd',
                                    driver_path / 'package' / 'cli.js',
                                ]
                                for p in possible_paths:
                                    if p.exists():
                                        driver_exe = p
                                        break

                            if driver_exe and driver_exe.exists():
                                # Found bundled driver
                                if driver_exe.suffix == '.js':
                                    # Need to run with node
                                    node_exe = driver_path / 'node.exe'
                                    if node_exe.exists():
                                        result = subprocess.run(
                                            [str(node_exe), str(driver_exe), "install", "chromium"],
                                            capture_output=False,
                                            text=True
                                        )
                                    else:
                                        raise Exception("Node.js not found in bundled files")
                                else:
                                    result = subprocess.run(
                                        [str(driver_exe), "install", "chromium"],
                                        capture_output=False,
                                        text=True
                                    )

                                if result.returncode != 0:
                                    raise Exception("Browser installation failed")
                            else:
                                raise Exception("Playwright driver not found in bundled files")
                        else:
                            raise Exception("PyInstaller _MEIPASS not found")

                    except Exception as install_error:
                        log(f"\n[yellow]자동 설치 실패: {install_error}[/yellow]\n")
                        log("[bold yellow]수동 설치가 필요합니다:[/bold yellow]\n")
                        log("1. 터미널/명령 프롬프트를 엽니다")
                        log("2. 다음 명령어를 실행:")
                        log("   [cyan]playwright install chromium[/cyan]\n")
                        log("또는 Python이 설치되어 있다면:")
                        log("   [cyan]python -m playwright install chromium[/cyan]\n")
                        if not log_callback:
                            sys.exit(1)
                        else:
                            raise
                else:
                    # Running as Python script - use normal method
                    import subprocess
                    result = subprocess.run(
                        [sys.executable, "-m", "playwright", "install", "chromium"],
                        capture_output=False,
                        text=True
                    )

                    if result.returncode != 0:
                        raise Exception("Browser installation failed")

                log("\n[green]OK[/green] Chromium 브라우저 설치 완료!")
                log("[green]OK[/green] Chromium browser installed successfully!")

    except Exception as e:
        log(f"\n[red]브라우저 설치 실패 (Browser installation failed)[/red]")
        log(f"[red]오류: {e}[/red]\n")
        log("[yellow]수동 설치 방법 (Manual installation):[/yellow]")
        log("\n[bold]옵션 1: Playwright CLI 사용 (권장)[/bold]")
        log("터미널/명령 프롬프트에서 실행:")
        log("   [cyan]playwright install chromium[/cyan]\n")
        log("[bold]옵션 2: Python 사용[/bold]")
        log("Python이 설치되어 있다면:")
        log("   [cyan]python -m playwright install chromium[/cyan]\n")
        log("[dim]자세한 내용은 INSTALL_GUIDE.txt를 참고하세요.[/dim]\n")
        if not log_callback:
            sys.exit(1)
        else:
            raise


def cleanup_temp_files():
    """Clean up temporary image files."""
    try:
        if os.path.exists(TEMP_IMAGE_DIR):
            shutil.rmtree(TEMP_IMAGE_DIR)
            console.print(f"[green]OK[/green] Cleaned up temporary files")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not clean up temp files: {e}[/yellow]")


def run_crawler(file: str, start_row: int, headless: bool, wait: float, verbose: bool, 
                scale: str = "1200",
                debug_mode: bool = False,
                save_pdf: bool = True,
                step_event = None,
                progress_callback=None, log_callback=None, stop_event=None,
                data_callback=None, save_request_event=None):
    """
    Run the crawler with optional callbacks for GUI integration.
    
    Args:
        file: Excel file path
        start_row: Starting row number
        headless: Run browser in headless mode
        wait: Page load wait time in seconds
        verbose: Verbose output
        scale: Map scale (e.g. "1200", "3000")
        debug_mode: Whether to run in debug mode (step-by-step)
        save_pdf: Whether to save PDF files (default: True)
        step_event: threading.Event for debug mode stepping
        progress_callback: Callback function(current_row, address, status) for progress updates
        log_callback: Callback function(message) for log messages
        stop_event: threading.Event to signal stop request
        data_callback: Callback function(row, data_dict) for data updates
        save_request_event: threading.Event to signal save request
    
    Returns:
        dict with keys: total_processed, total_success, total_failed, elapsed_time, error
    """
    result = {
        "total_processed": 0,
        "total_success": 0,
        "total_failed": 0,
        "elapsed_time": 0,
        "error": None
    }
    
    def log(message):
        if log_callback:
            try:
                log_callback(message)
            except Exception as e:
                # If log_callback fails, try to log the error
                import traceback
                error_msg = f"Error in log_callback: {e}\n{traceback.format_exc()}"
                try:
                    log_callback(error_msg)
                except:
                    pass
        else:
            try:
                console.print(message)
            except Exception as e:
                # Fallback to regular print if console.print fails
                print(f"Console print error: {e}")
                print(str(message))
    
    def progress(row, address, status, message=None):
        if progress_callback:
            progress_callback(row, address, status, message)
            
    def wait_for_step(msg):
        """Wait for user input in debug mode."""
        if debug_mode and step_event:
            log(f"\n[bold yellow]DEBUG: {msg}[/bold yellow]")
            log("[dim]Waiting for user to press 'Next'...[/dim]")
            step_event.wait()
            step_event.clear()
            log("[dim]Resuming...[/dim]\n")
    
    try:
        # Log startup information
        log("=" * 50)
        log("크롤링 시작 (Starting crawler)")
        log(f"GUI 모드: {os.environ.get('EUMCRAWL_GUI_MODE', '0') == '1'}")
        log(f"파일: {file}")
        log(f"시작 행: {start_row}")
        log(f"지적도 축적: 1/{scale}")
        log(f"PDF 저장: {save_pdf}")
        log(f"디버그 모드: {debug_mode}")
        log("=" * 50)
        
        # Setup Playwright
        if verbose:
            log("[cyan]Checking Playwright setup...[/cyan]")
        try:
            log("Playwright 설정 시작...")
            setup_playwright(log_callback=log_callback)
            log("Playwright 설정 완료")
        except Exception as e:
            error_msg = f"Playwright 설정 오류: {e}"
            log(error_msg)
            import traceback
            log(f"상세 오류:\n{traceback.format_exc()}")
            result["error"] = error_msg
            return result

        # Initialize handlers
        try:
            log("Excel 핸들러 초기화 중...")
            excel_handler = ExcelHandler(file)
            if not excel_handler.open():
                error_msg = "[red]Failed to open Excel file.[/red]"
                log(error_msg)
                result["error"] = "Failed to open Excel file"
                return result
            log("Excel 파일 열기 성공")
        except Exception as e:
            error_msg = f"Excel 핸들러 초기화 오류: {e}"
            log(error_msg)
            import traceback
            log(f"상세 오류:\n{traceback.format_exc()}")
            result["error"] = error_msg
            return result

        try:
            log("스크래퍼 초기화 중...")
            scraper = RealEstateScraper(headless=headless, wait_time=wait, log_callback=log)
            log("브라우저 시작 중...")
            if not scraper.start():
                excel_handler.close()
                error_msg = "[red]Failed to start browser.[/red]"
                log(error_msg)
                result["error"] = "Failed to start browser"
                return result
            log("브라우저 시작 성공")
            
            # Wait 1: After browser start
            wait_for_step("브라우저 시작 완료. 다음 단계: 주소 검증")
            
        except Exception as e:
            error_msg = f"스크래퍼 초기화 오류: {e}"
            log(error_msg)
            import traceback
            log(f"상세 오류:\n{traceback.format_exc()}")
            if 'excel_handler' in locals():
                excel_handler.close()
            result["error"] = error_msg
            return result

        # Statistics
        total_processed = 0
        total_success = 0
        total_failed = 0
        start_time = time.time()

        try:
            current_row = start_row

            log(f"\n[bold]Starting crawl from row {start_row}[/bold]\n")
            
            # Phase 1: Validation
            log("=" * 30)
            log("1단계: 주소 유효성 검증 시작 (Phase 1: Validation)")
            log("=" * 30)
            
            valid_rows = []
            rows_since_save = 0  # Counter for batch saving
            
            while True:
                # Check for stop request
                if stop_event and stop_event.is_set():
                    log("\n[yellow]Stopped by user[/yellow]")
                    break

                # Read address
                address = excel_handler.read_address(current_row)

                if not address:
                    if verbose:
                        log(f"[dim]Row {current_row}: Empty, finished validation[/dim]")
                    break

                progress(current_row, address, "processing", "검증 중...")
                
                # Check validity via Ajax
                count, pnu = scraper.check_address_count(address, verbose=verbose)
                
                # Calculate Sequence ID (1-based from start_row)
                sequence_id = current_row - start_row + 1

                if count >= 1:
                    valid_rows.append((current_row, address, pnu, sequence_id))
                    
                    # Write PNU and ID to Excel immediately
                    excel_handler.write_data(current_row, {"pnu": pnu, "id": str(sequence_id)})
                    if data_callback:
                        data_callback(current_row, {"pnu": pnu, "id": str(sequence_id)})
                    
                    # Mark as validated in GUI with PNU
                    if count > 1:
                        status_msg = f"검증 완료: {count}건 중 1번째|{pnu}"
                        log(f"[green]Row {current_row}: Validated ({address}) - Found {count} matches, using first - PNU: {pnu}[/green]")
                    else:
                        status_msg = f"검증 완료: 유효함|{pnu}"
                        log(f"[green]Row {current_row}: Validated ({address}) - PNU: {pnu}[/green]")
                        
                    progress(current_row, address, "processing", status_msg)
                else:
                    # Handle invalid rows
                    if count == 0:
                        reason = "유효주소 없음"
                    else:
                        reason = "검증 오류"
                    
                    log(f"[red]Row {current_row}: Failed validation - {reason}[/red]")
                    
                    # Write error to Excel
                    error_data = {
                        "result": "검증실패",
                        "details": reason,
                        "id": str(sequence_id)
                    }
                    excel_handler.write_data(current_row, error_data)
                    if data_callback:
                        data_callback(current_row, error_data)
                    if data_callback:
                        data_callback(current_row, error_data)
                    # Don't save every row to prevent file corruption
                    # excel_handler.save()
                    
                    # But do save every 5 invalid rows to avoid data loss
                    rows_since_save += 1
                    if rows_since_save >= 5:
                        if excel_handler.save():
                            rows_since_save = 0
                        else:
                            log(f"[yellow]Warning: Failed to save Excel file (Row {current_row})[/yellow]")
                    
                    progress(current_row, address, "failed", reason)
                    total_failed += 1
                
                current_row += 1
                
                # Check for manual save request
                if save_request_event and save_request_event.is_set():
                    log("[dim]Saving Excel file...[/dim]")
                    excel_handler.save()
                    save_request_event.clear()
                    log("[dim]Saved.[/dim]")
            
            # Save after validation phase is complete
            if rows_since_save > 0:
                excel_handler.save()
                rows_since_save = 0
            
            # Wait 2: After validation
            wait_for_step(f"주소 검증 완료 (유효: {len(valid_rows)}건). 다음 단계: 크롤링 시작")
                
            # Phase 2: Scraping
            if not (stop_event and stop_event.is_set()):
                log("\n" + "=" * 30)
                log(f"2단계: 크롤링 시작 (대상 {len(valid_rows)}건) (Phase 2: Scraping)")
                log("=" * 30 + "\n")
                
                for row, address, pnu, sequence_id in valid_rows:
                    if stop_event and stop_event.is_set():
                        log("\n[yellow]Stopped by user[/yellow]")
                        break
                    
                    # Wait 3: Before each row scraping
                    wait_for_step(f"Row {row} (ID {sequence_id}) ({address}) 크롤링 시작")
                        
                    progress(row, address, "processing", "크롤링 중...")
                    log(f"[bold cyan]Row {row} (ID {sequence_id}):[/bold cyan] {address}")

                    # Scrape data
                    row_start_time = time.time()
                    
                    # Search address
                    success, search_msg = scraper.search_address(address, pnu=pnu, scale=scale)
                    if not success:
                        error_reason = f"주소 검색 실패 ({search_msg})"
                        excel_handler.write_data(row, {"result": "실패", "details": error_reason})
                        total_failed += 1
                        progress(row, address, "failed", error_reason)
                        log(f"[red]Failed[/red] Row {row}: {error_reason}\n")
                        continue
                    
                    # Extract data
                    data = scraper.extract_data()
                    
                    # Download image
                    """
                    이전 코드
                    image_path = None
                    if scale == "1200":
                        # 기본 축척(1/1200)만 일반 다운로드
                        image_path = scraper.download_image(sequence_id, address, scale="1200")
                    elif pnu:
                        # 나머지 축척은 모두 팝업창 다운로드 (PNU 필요)
                        image_path = scraper.download_image_from_popup(
                            sequence_id, address, pnu, scale, debug_mode, step_event
                        )
                    else:
                        # PNU가 없으면 일반 다운로드로 fallback
                        image_path = scraper.download_image(sequence_id, address, scale="1200")
                    """
                    image_path = scraper.download_image(sequence_id, address, scale=scale)
                    
                    # Save PDF
                    if save_pdf:
                        scraper.save_pdf(sequence_id, address, scale=scale)
                    else:
                        log(f"[dim]Row {row}: PDF save disabled[/dim]")
                    
                    row_elapsed = time.time() - row_start_time

                    if data:
                        # Add image path to data
                        if image_path:
                            data["image_path"] = image_path
                        else:
                            log(f"[yellow]Row {row}: Image path is None (Download failed or not found)[/yellow]")
                        
                        # Set image status (Y/N)
                        if "image_path" in data and data["image_path"]:
                            data["image_status"] = "Y"
                        else:
                            data["image_status"] = "N"
                            log(f"[dim]Row {row}: Image Status set to N[/dim]")
                        
                        # Write data to Excel
                        excel_handler.write_data(row, data)
                        if data_callback:
                            data_callback(row, data)

                        # Insert image if available
                        if "image_path" in data and os.path.exists(data["image_path"]):
                            excel_handler.insert_image(row, data["image_path"])

                        # Save Excel file periodically (every 5 rows)
                        # Frequent saving causes file corruption with openpyxl images
                        rows_since_save += 1
                        if rows_since_save >= 5:
                            log("[dim]Auto-saving Excel file...[/dim]")
                            if excel_handler.save():
                                rows_since_save = 0
                                log("[dim]Saved.[/dim]")
                            else:
                                log(f"[red]Warning: Failed to save Excel file for row {row}. (File might be open?)[/red]")
                        
                        # Check for manual save request
                        if save_request_event and save_request_event.is_set():
                            log("[dim]Saving Excel file (Manual)...[/dim]")
                            if excel_handler.save():
                                rows_since_save = 0
                                save_request_event.clear()
                                log("[dim]Saved.[/dim]")
                            else:
                                log("[red]Manual save failed.[/red]")

                        total_success += 1
                        progress(row, address, "success", f"{row_elapsed:.1f}초")
                        log(f"[green]OK[/green] Row {row} completed\n")

                        if verbose:
                            # Print extracted data
                            table = Table(show_header=True, header_style="bold magenta")
                            table.add_column("Field", style="cyan")
                            table.add_column("Value", style="green")

                            for key, value in data.items():
                                if key != "image_path":
                                    table.add_row(key, str(value)[:50])

                            console.print(table)
                            console.print()
                    else:
                        # This happens if UI search fails or extraction fails
                        # Even though we validated, network issues or timeouts can happen
                        error_reason = "크롤링 실패 (상세 로그 확인)"
                        excel_handler.write_data(row, {"result": "실패", "details": error_reason})
                        
                        rows_since_save += 1
                        if rows_since_save >= 5:
                            excel_handler.save()
                            rows_since_save = 0
                        
                        total_failed += 1
                        progress(row, address, "failed", error_reason)
                        log(f"[red]FAIL[/red] Row {row} failed\n")
                        
                    total_processed += 1

        except KeyboardInterrupt:
            log("\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            error_msg = f"\n[red]Unexpected error: {e}[/red]"
            log(error_msg)
            if verbose:
                import traceback
                log(traceback.format_exc())
            result["error"] = str(e)
            # progress(current_row, address, "failed", str(e)) # current_row/address might not be defined here
        finally:
            # Cleanup
            log("Cleaning up...")
            if 'scraper' in locals():
                scraper.close()
            if 'excel_handler' in locals():
                # Ensure final save
                try:
                    time.sleep(0.5) # Wait for filesystem
                    log("Finalizing Excel file...")
                    if not excel_handler.save():
                        log(f"[red]Error: Failed to save final Excel file. Check if file is open.[/red]")
                    else:
                        log("[green]OK[/green] Excel saved successfully.")
                except Exception as e:
                    log(f"[red]Error during final save: {e}[/red]")
                excel_handler.close()
            cleanup_temp_files()

            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            result["total_processed"] = total_processed
            result["total_success"] = total_success
            result["total_failed"] = total_failed
            result["elapsed_time"] = elapsed_time

            # Print summary
            log("\n" + "="*50)
            summary = (
                f"[bold]Processing Complete[/bold]\n\n"
                f"Total Processed: [cyan]{total_processed}[/cyan]\n"
                f"Success: [green]{total_success}[/green]\n"
                f"Failed: [red]{total_failed}[/red]\n"
                f"Time Elapsed: [yellow]{elapsed_time:.1f}s[/yellow]"
            )
            # For GUI, just log the summary text directly
            # For CLI, use Panel for better formatting
            if log_callback:
                log(summary)
            else:
                try:
                    log(Panel.fit(summary, border_style="green"))
                except Exception as e:
                    # Fallback if Panel fails
                    log(summary)
                    print(f"Panel error: {e}")
    
    except Exception as e:
        error_msg = f"[red]Error: {e}[/red]"
        log(error_msg)
        import traceback
        full_traceback = traceback.format_exc()
        log(f"전체 스택 트레이스:\n{full_traceback}")
        result["error"] = str(e)
        result["traceback"] = full_traceback
    
    return result


@click.command()
@click.option(
    "--file",
    "-f",
    required=True,
    type=click.Path(exists=True),
    help="Path to Excel file",
)
@click.option(
    "--start-row",
    "-s",
    default=DEFAULT_START_ROW,
    type=int,
    help=f"Starting row number (default: {DEFAULT_START_ROW})",
)
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Run browser in headless mode (default: headless)",
)
@click.option(
    "--wait",
    "-w",
    default=DEFAULT_WAIT_TIME,
    type=float,
    help=f"Page load wait time in seconds (default: {DEFAULT_WAIT_TIME})",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
def main(file: str, start_row: int, headless: bool, wait: float, verbose: bool):
    """
    Real Estate Information Crawler

    Crawls real estate information from eum.go.kr based on addresses in Excel file.
    """
    # Print banner
    console.print(Panel.fit(
        f"[bold cyan]부동산 정보 크롤링 프로그램 v{VERSION}[/bold cyan]\n"
        f"[dim]Real Estate Information Crawler v{VERSION}[/dim]",
        border_style="cyan"
    ))
    
    # Run crawler with CLI callbacks (no log_callback for CLI)
    run_crawler(file, start_row, headless, wait, verbose, 
                progress_callback=None, log_callback=None, stop_event=None)


if __name__ == "__main__":
    main()
