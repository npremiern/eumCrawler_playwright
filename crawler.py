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

from config import DEFAULT_START_ROW, DEFAULT_WAIT_TIME, TEMP_IMAGE_DIR
from excel_handler import ExcelHandler
from scraper import RealEstateScraper

# Set console to use safe encoding for Windows
console = Console(legacy_windows=False)


def setup_playwright():
    """Check and setup Playwright browsers."""
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
                console.print("[cyan]Extracting Chromium browser from package...[/cyan]")
                console.print("[cyan]패키지에서 Chromium 브라우저 압축 해제 중...[/cyan]")

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
                            console.print("[green]OK[/green] Browser extracted successfully!")
                            console.print("[green]OK[/green] 브라우저 압축 해제 완료!")
                            break
                except Exception as extract_error:
                    console.print(f"[yellow]Warning: Failed to extract browser: {extract_error}[/yellow]")

        # Try to import and use playwright
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                # Try to launch browser to check if it's installed
                browser = p.chromium.launch(headless=True)
                browser.close()
            except Exception as e:
                # Browser not found, install it
                console.print("\n" + "="*60)
                console.print("[bold yellow]첫 실행 설정 (First-time Setup)[/bold yellow]")
                console.print("="*60)
                console.print("[cyan]Chromium 브라우저를 다운로드합니다...[/cyan]")
                console.print("[cyan]Downloading Chromium browser...[/cyan]")
                console.print("[dim]크기: 약 200MB | Size: ~200MB[/dim]")
                console.print("[dim]소요 시간: 3-5분 | Time: 3-5 minutes[/dim]")
                console.print("="*60 + "\n")

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
                        console.print(f"\n[yellow]자동 설치 실패: {install_error}[/yellow]\n")
                        console.print("[bold yellow]수동 설치가 필요합니다:[/bold yellow]\n")
                        console.print("1. 터미널/명령 프롬프트를 엽니다")
                        console.print("2. 다음 명령어를 실행:")
                        console.print("   [cyan]playwright install chromium[/cyan]\n")
                        console.print("또는 Python이 설치되어 있다면:")
                        console.print("   [cyan]python -m playwright install chromium[/cyan]\n")
                        sys.exit(1)
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

                console.print("\n[green]OK[/green] Chromium 브라우저 설치 완료!")
                console.print("[green]OK[/green] Chromium browser installed successfully!")

    except Exception as e:
        console.print(f"\n[red]브라우저 설치 실패 (Browser installation failed)[/red]")
        console.print(f"[red]오류: {e}[/red]\n")
        console.print("[yellow]수동 설치 방법 (Manual installation):[/yellow]")
        console.print("\n[bold]옵션 1: Playwright CLI 사용 (권장)[/bold]")
        console.print("터미널/명령 프롬프트에서 실행:")
        console.print("   [cyan]playwright install chromium[/cyan]\n")
        console.print("[bold]옵션 2: Python 사용[/bold]")
        console.print("Python이 설치되어 있다면:")
        console.print("   [cyan]python -m playwright install chromium[/cyan]\n")
        console.print("[dim]자세한 내용은 INSTALL_GUIDE.txt를 참고하세요.[/dim]\n")
        sys.exit(1)


def cleanup_temp_files():
    """Clean up temporary image files."""
    try:
        if os.path.exists(TEMP_IMAGE_DIR):
            shutil.rmtree(TEMP_IMAGE_DIR)
            console.print(f"[green]OK[/green] Cleaned up temporary files")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not clean up temp files: {e}[/yellow]")


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
        "[bold cyan]부동산 정보 크롤링 프로그램[/bold cyan]\n"
        "[dim]Real Estate Information Crawler v1.0[/dim]",
        border_style="cyan"
    ))

    # Setup Playwright
    if verbose:
        console.print("[cyan]Checking Playwright setup...[/cyan]")
    setup_playwright()

    # Initialize handlers
    excel_handler = ExcelHandler(file)
    if not excel_handler.open():
        console.print("[red]Failed to open Excel file. Exiting.[/red]")
        sys.exit(1)

    scraper = RealEstateScraper(headless=headless, wait_time=wait)
    if not scraper.start():
        excel_handler.close()
        console.print("[red]Failed to start browser. Exiting.[/red]")
        sys.exit(1)

    # Statistics
    total_processed = 0
    total_success = 0
    total_failed = 0
    start_time = time.time()

    try:
        current_row = start_row

        console.print(f"\n[bold]Starting crawl from row {start_row}[/bold]\n")

        while True:
            # Read address
            address = excel_handler.read_address(current_row)

            if not address:
                if verbose:
                    console.print(f"[dim]Row {current_row}: Empty, stopping[/dim]")
                break

            console.print(f"[bold cyan]Row {current_row}:[/bold cyan] {address}")

            # Scrape data
            with console.status(f"[bold green]Scraping row {current_row}...", spinner="dots"):
                data = scraper.scrape_address(address, current_row)

            if data:
                # Write data to Excel
                excel_handler.write_data(current_row, data)

                # Insert image if available
                if "image_path" in data and os.path.exists(data["image_path"]):
                    excel_handler.insert_image(current_row, data["image_path"])

                # Save Excel file after each row
                excel_handler.save()

                total_success += 1
                console.print(f"[green]OK[/green] Row {current_row} completed\n")

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
                total_failed += 1
                console.print(f"[red]FAIL[/red] Row {current_row} failed\n")

            total_processed += 1
            current_row += 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
    finally:
        # Cleanup
        scraper.close()
        excel_handler.close()
        cleanup_temp_files()

        # Print summary
        elapsed_time = time.time() - start_time

        console.print("\n" + "="*50)
        console.print(Panel.fit(
            f"[bold]Processing Complete[/bold]\n\n"
            f"Total Processed: [cyan]{total_processed}[/cyan]\n"
            f"Success: [green]{total_success}[/green]\n"
            f"Failed: [red]{total_failed}[/red]\n"
            f"Time Elapsed: [yellow]{elapsed_time:.1f}s[/yellow]",
            border_style="green"
        ))


if __name__ == "__main__":
    main()
