"""GUI application for real estate information crawler."""

# IMPORTANT: Set GUI mode BEFORE any imports
# This must be the very first thing to avoid Rich Console initialization errors
import os
os.environ['EUMCRAWL_GUI_MODE'] = '1'

import sys
import threading
import time
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional

# Import crawler functions (after setting environment variable)
from crawler import run_crawler, setup_playwright
from config import DEFAULT_START_ROW, DEFAULT_WAIT_TIME, TEMPLATE_HEADERS, VERSION
from excel_handler import ExcelHandler
class CrawlerGUI:
    """GUI application for the real estate crawler."""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"토지이용계획확인원 데이터가져오기 v{VERSION}")
        
        # Config file for window settings
        from config import BASE_DIR
        self.config_file = os.path.join(BASE_DIR, "gui_config.json")
        
        # Load saved window geometry or use default
        saved_geometry = self.load_window_geometry()
        if saved_geometry:
            self.root.geometry(saved_geometry)
        else:
            self.root.geometry("800x900")
        
        self.root.resizable(True, True)
        
        # Variables
        self.excel_file = tk.StringVar()
        self.start_row = tk.IntVar(value=DEFAULT_START_ROW)
        self.headless = tk.BooleanVar(value=True)
        self.wait_time = tk.DoubleVar(value=DEFAULT_WAIT_TIME)
        self.verbose = tk.BooleanVar(value=False)
        self.scale_options = {
            "축적 1/1200 (기본)": "1200",
            "축적 1 / 1": "1", "축적 1 / 500": "500", "축적 1 / 600": "600", 
            "축적 1 / 1000": "1000", "축적 1 / 2400": "2400", "축적 1 / 3000": "3000", 
            "축적 1 / 6000": "6000", "축적 1 / 12000": "12000"
        }
        self.scale = tk.StringVar(value="축적 1/1200 (기본)")
        self.save_pdf = tk.BooleanVar(value=True)
        self.debug_mode = tk.BooleanVar(value=False)
        
        # State
        self.is_dark_theme = False
        self.is_running = False
        self.stop_event = threading.Event()
        self.step_event = threading.Event()
        self.save_request_event = threading.Event()
        self.scraper = None
        self.browser_ready = False
        self.start_crawling_event = threading.Event()
        self.shutdown_event = threading.Event()
        
        self.pnu_fetch_queue = queue.Queue()
        self.fetch_pnu_cancel = threading.Event()
        
        # UI Elements referencing
        self.log_frame = None
        self.log_toggle_btn = None
        self.log_visible = False
        
        # Statistics
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = None
        
        # Create UI
        self.create_widgets()
        
        # Center window
        self.center_window()
        
        # Disable start button until browser is ready
        self.start_btn.config(state=tk.DISABLED, text="로딩 중...")
        
        # Start browser in background
        threading.Thread(target=self.init_browser_thread, daemon=True).start()

    def init_browser_thread(self):
        """Initialize browser in background on startup."""
        self.log("브라우저를 백그라운드에서 초기화합니다...")
        try:
            from scraper import RealEstateScraper
            setup_playwright(log_callback=self.log_callback) # Use log_callback to strip rich tags
            self.scraper = RealEstateScraper(headless=self.headless.get(), wait_time=self.wait_time.get(), log_callback=self.log_callback)
            if self.scraper.start():
                self.browser_ready = True
                self.log("▶ 브라우저 초기화 완료! 이제 크롤링을 시작할 수 있습니다.")
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL, text="시작"))
            else:
                self.log("브라우저 초기화 실패")
                self.root.after(0, lambda: self.start_btn.config(state=tk.DISABLED, text="초기화 실패"))
                return
                
            # persistent loop to handle scraping requests on the SAME thread
            while not self.shutdown_event.is_set():
                if self.start_crawling_event.is_set():
                    self.start_crawling_event.clear()
                    self._execute_crawler_job()
                else:
                    try:
                        # Try to get a PNU fetching task with a short timeout to stay responsive
                        row, address = self.pnu_fetch_queue.get(timeout=0.2)
                        if self.fetch_pnu_cancel.is_set():
                            continue
                        self._fetch_missing_pnu_job(row, address)
                    except queue.Empty:
                        pass
                    
        except Exception as e:
            self.log(f"브라우저 초기화 중 오류: {e}")
            
        finally:
            if self.scraper:
                try:
                    self.scraper.close()
                except Exception:
                    pass
        
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_window_geometry(self):
        """Load saved window geometry from config file."""
        try:
            if os.path.exists(self.config_file):
                import json
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('window_geometry')
        except Exception as e:
            print(f"Failed to load window geometry: {e}")
        return None
        
    def _fetch_missing_pnu_job(self, row, address):
        """Fetch PNU for a specific row in the background and update Excel/GUI."""
        if not self.scraper:
            return
        
        # Don't run fetching logic if crawler is currently active
        if self.is_running:
            return
            
        try:
            count, pnu = self.scraper.check_address_count(address, verbose=False)
            if pnu:
                self.log(f"[dim]PNU 자동 검색 성공 - {address} -> {pnu}[/dim]")
                # Update excel file
                file_path = self.excel_file.get()
                if file_path and os.path.exists(file_path):
                    # Sleep slightly to prevent rapid file locks
                    time.sleep(0.1)
                    handler = ExcelHandler(file_path)
                    if handler.open():
                        handler.write_data(row, {"pnu": pnu})
                        handler.save()
                        handler.close()
                # Update GUI
                self.update_data(row, {"pnu": pnu})
        except Exception as e:
            pass # Ignore errors silently here since background fetching error shouldn't disturb using the app
    
    def save_window_geometry(self):
        """Save current window geometry to config file."""
        try:
            import json
            geometry = self.root.geometry()
            config = {'window_geometry': geometry}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save window geometry: {e}")
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text=f"토지이용계획확인원 데이터가져오기 v{VERSION}",
            font=("맑은 고딕", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Excel 파일 선택", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="파일:").grid(row=0, column=0, padx=5, sticky=tk.W)
        file_entry = ttk.Entry(file_frame, textvariable=self.excel_file, width=50)
        file_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(file_frame, text="찾아보기...", command=self.browse_file)
        browse_btn.grid(row=0, column=2, padx=5)
        
        template_btn = ttk.Button(file_frame, text="양식 다운받기", command=self.download_template)
        template_btn.grid(row=0, column=3, padx=5)
        
        # Control Area (Settings + Buttons)
        control_area = ttk.Frame(main_frame)
        control_area.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        control_area.columnconfigure(0, weight=6)  # Settings takes 60%
        control_area.columnconfigure(1, weight=4)  # Buttons takes 40%
        
        # Settings (Left)
        settings_frame = ttk.LabelFrame(control_area, text="설정", padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Quick Settings: PDF & Scale
        # PDF Checkbox
        pdf_check = ttk.Checkbutton(
            settings_frame,
            text="PDF 다운로드",
            variable=self.save_pdf
        )
        pdf_check.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Scale (Grouped next to PDF with some spacing)
        ttk.Label(settings_frame, text="지적도 축적 :").grid(row=0, column=1, padx=(10, 5), sticky=tk.W)
        scale_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.scale,
            values=list(self.scale_options.keys()),
            state="readonly",
            width=18
        )
        scale_combo.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # Theme Toggle Button (Right of Scale)
        self.theme_btn = ttk.Button(
            settings_frame,
            text="☀️ 라이트",
            width=8,
            command=self.toggle_theme
        )
        self.theme_btn.grid(row=0, column=3, padx=5, pady=5, sticky=tk.E)

        # Gear Icon Button (Right of Theme toggle)
        settings_btn = ttk.Button(
            settings_frame,
            text="⚙", # Unicode gear icon
            width=3,
            command=self.open_settings_popup
        )
        settings_btn.grid(row=0, column=4, padx=5, pady=5, sticky=tk.E)

        # Buttons (Right, Horizontal)
        button_frame = ttk.Frame(control_area, padding="10")
        button_frame.grid(row=0, column=1, sticky=(tk.E)) # Align right
        
        self.start_btn = ttk.Button(
            button_frame,
            text="시작",
            style="Accent.TButton", # Adds nice default accent color point to main action
            command=self.start_crawler,
            width=10
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="중지",
            command=self.stop_crawler,
            state=tk.DISABLED,
            width=10
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(
            button_frame,
            text="저장",
            command=self.save_data,
            state=tk.DISABLED,
            width=10
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Data Table (Treeview)
        table_frame = ttk.LabelFrame(main_frame, text="작업 목록", padding="10")
        table_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=2)  # Give more weight to table
        
        columns = ("ID", "ADDRESS", "RESULT", "DETAILS", "PNU", "CLASS", "AREA", "JIGA", "JIGA_YEAR", "ZONE1", "ZONE2", "REGULATION", "COMBINED", "IMAGE")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.tree.heading("ID", text="NO")
        self.tree.heading("ADDRESS", text="주소(입력)")
        self.tree.heading("RESULT", text="결과")
        self.tree.heading("DETAILS", text="상세내용")
        self.tree.heading("PNU", text="PNU")
        self.tree.heading("CLASS", text="지목")
        self.tree.heading("AREA", text="면적")
        self.tree.heading("JIGA", text="지가")
        self.tree.heading("JIGA_YEAR", text="지가연도")
        self.tree.heading("ZONE1", text="지역지구1")
        self.tree.heading("ZONE2", text="지역지구2")
        self.tree.heading("REGULATION", text="토지이용규제")
        self.tree.heading("COMBINED", text="통합규제")
        self.tree.heading("IMAGE", text="이미지여부")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("ADDRESS", width=200)
        self.tree.column("RESULT", width=80, anchor="center")
        self.tree.column("DETAILS", width=150)
        self.tree.column("PNU", width=120, anchor="center")
        self.tree.column("CLASS", width=80, anchor="center")
        self.tree.column("AREA", width=80, anchor="e")
        self.tree.column("JIGA", width=80, anchor="e")
        self.tree.column("JIGA_YEAR", width=80, anchor="center")
        self.tree.column("ZONE1", width=100)
        self.tree.column("ZONE2", width=100)
        self.tree.column("REGULATION", width=100)
        self.tree.column("COMBINED", width=150)
        self.tree.column("IMAGE", width=80, anchor="center")
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.tree.configure(yscroll=v_scrollbar.set, xscroll=h_scrollbar.set)
        
        # Bind events for copying
        self.tree.bind("<Control-c>", self.copy_selection)
        # Windows/Linux right-click is <Button-3>, macOS is <Button-2> or <Button-3>
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Progress & Statistics (combined in one line)
        status_frame = ttk.LabelFrame(main_frame, text="진행 상황 및 통계", padding="10")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        status_frame.columnconfigure(1, weight=1)
        
        # Progress bar (left side, fixed width)
        self.progress_bar = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=150
        )
        self.progress_bar.grid(row=0, column=0, padx=(0, 10))
        
        # Progress text (middle, expandable)
        self.progress_var = tk.StringVar(value="대기 중...")
        ttk.Label(status_frame, textvariable=self.progress_var).grid(row=0, column=1, sticky=tk.W)
        
        # Statistics (right side)
        self.stats_label = ttk.Label(
            status_frame,
            text="처리: 0 | 성공: 0 | 실패: 0 | 시간: 0s",
            font=("맑은 고딕", 9)
        )
        self.stats_label.grid(row=0, column=2, padx=(10, 0))
        
        # Log Control (Button to toggle log)
        log_control_frame = ttk.Frame(main_frame)
        log_control_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.log_toggle_btn = ttk.Button(
            log_control_frame,
            text="로그 보이기 ▼",
            command=self.toggle_log
        )
        self.log_toggle_btn.pack(side=tk.LEFT)

        # Log output (Hidden by default)
        self.log_frame = ttk.LabelFrame(main_frame, text="로그", padding="10")
        # Don't grid it initially
        # self.log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)
        
        # Use row 6 for log frame now
        main_frame.rowconfigure(6, weight=0) # Initially 0 weight
        
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=10,
            width=100,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="준비")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def copy_selection(self, event=None):
        """Copy selected rows in Treeview to clipboard."""
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        clipboard_data = []
        for item in selected_items:
            values = self.tree.item(item, 'values')
            # Convert tuple to tab-separated string
            row_data = '\t'.join(str(v) for v in values)
            clipboard_data.append(row_data)
        
        # Join multiple rows with newline
        final_text = '\n'.join(clipboard_data)
        
        self.root.clipboard_clear()
        self.root.clipboard_append(final_text)
        
    def show_context_menu(self, event):
        """Show context menu on right click in treeview."""
        # Check if anything is selected
        selected_items = self.tree.selection()
        if not selected_items:
            # If nothing was selected, select the row under cursor
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
            else:
                return
                
        # Create popup menu
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="복사 (Copy)", command=self.copy_selection)
        menu.post(event.x_root, event.y_root)

    def toggle_theme(self):
        """Toggle between dark and light themes using sv_ttk."""
        import sv_ttk
        if self.is_dark_theme:
            sv_ttk.set_theme("light")
            self.theme_btn.config(text="☀️ 라이트")
            self.is_dark_theme = False
        else:
            sv_ttk.set_theme("dark")
            self.theme_btn.config(text="🌙 다크")
            self.is_dark_theme = True

    def toggle_log(self):
        """Toggle log visibility."""
        if self.log_visible:
            self.log_frame.grid_remove()
            self.log_toggle_btn.config(text="로그 보이기 ▼")
            # Shrink the log row
            self.log_frame.master.rowconfigure(6, weight=0)
            self.log_visible = False
        else:
            self.log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
            self.log_toggle_btn.config(text="로그 숨기기 ▲")
            # Expand the log row
            self.log_frame.master.rowconfigure(6, weight=1)
            self.log_visible = True
            
    def open_settings_popup(self):
        """Open settings popup dialog."""
        popup = tk.Toplevel(self.root)
        popup.title("상세 설정")
        popup.geometry("400x350")
        
        # Center popup relative to main window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 175
        popup.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(popup, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Start Row
        row_frame = ttk.Frame(frame)
        row_frame.pack(fill=tk.X, pady=10)
        ttk.Label(row_frame, text="시작 행 번호:").pack(side=tk.LEFT)
        ttk.Spinbox(
            row_frame, from_=1, to=10000, textvariable=self.start_row, width=10
        ).pack(side=tk.RIGHT)
        
        # Wait Time
        wait_frame = ttk.Frame(frame)
        wait_frame.pack(fill=tk.X, pady=10)
        ttk.Label(wait_frame, text="페이지 대기 시간(초):").pack(side=tk.LEFT)
        ttk.Spinbox(
            wait_frame, from_=1.0, to=60.0, increment=0.5, textvariable=self.wait_time, width=10
        ).pack(side=tk.RIGHT)
        
        # Headless (Moved from main)
        ttk.Checkbutton(
            frame, text="헤드리스 모드 (브라우저 숨김)", variable=self.headless
        ).pack(anchor=tk.W, pady=5)
        
        # Checkboxes
        ttk.Checkbutton(
            frame, text="상세 로그 출력 (Verbose)", variable=self.verbose
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Checkbutton(
            frame, text="디버그 모드 (단계별 실행)", variable=self.debug_mode
        ).pack(anchor=tk.W, pady=5)
        
        # Close Button
        ttk.Button(frame, text="닫기", command=popup.destroy).pack(pady=20)
        
    def reset_ui(self):
        """Reset all UI elements and internal state except settings."""
        # Clear tree view
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset statistics
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = None
        
        # Reset progress
        self.progress_var.set("대기 중...")
        self.progress_bar.stop()
        
        # Reset status
        self.status_var.set("준비")
        
        # Update stats display
        self.update_stats()
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Reset events
        self.stop_event.clear()
        self.step_event.clear()
        self.save_request_event.clear()
        
        # Reset running state
        self.is_running = False
        
        # Reset buttons
        self.start_btn.config(text="시작", command=self.start_crawler, state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        
    def browse_file(self):
        """Browse for Excel file."""
        filename = filedialog.askopenfilename(
            title="Excel 파일 선택",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.excel_file.set(filename)
            self.log(f"파일 선택: {filename}")
            
            # Reset all UI and state before loading new file
            self.reset_ui()
            
            # Load file data into table
            self.load_excel_data()
            
    def download_template(self):
        """Download Excel template."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="eum_crawler_template.xlsx",
            title="양식 다운로드"
        )
        if file_path:
            if ExcelHandler.create_template(file_path):
                messagebox.showinfo("성공", "양식 파일이 저장되었습니다.")
            else:
                messagebox.showerror("오류", "양식 파일 저장에 실패했습니다.")

    def save_data(self):
        """Request to save data to Excel."""
        if self.is_running:
            self.save_request_event.set()
        else:
            messagebox.showinfo("알림", "크롤링 중일 때만 저장할 수 있습니다.\n(종료 시 자동 저장됩니다)")

    def update_data(self, row, data):
        """Update data in Treeview (Thread-safe)."""
        self.root.after(0, lambda: self._update_data_impl(row, data))

    def _update_data_impl(self, row, data):
        """Actual data update implementation."""
        try:
            self.log(f"[dim][DEBUG] Updating row {row}, data keys: {list(data.keys())}[/dim]")
            iid = str(row)
            if self.tree.exists(iid):
                current_values = list(self.tree.item(iid, "values"))
                self.log(f"[dim][DEBUG] Current values length: {len(current_values)}[/dim]")
                # ID=0, ADDRESS=1, RESULT=2, DETAILS=3, PNU=4, CLASS=5, AREA=6, JIGA=7, JIGA_YEAR=8, ZONE1=9, ZONE2=10, REGULATION=11, COMBINED=12, IMAGE=13
                
                if "id" in data: current_values[0] = data["id"]
                if "result" in data: current_values[2] = data["result"]
                if "details" in data: current_values[3] = data["details"]
                if "pnu" in data: current_values[4] = data["pnu"]
                if "present_class" in data: 
                    current_values[5] = data["present_class"]
                    self.log(f"[dim][DEBUG] Set CLASS to: {data['present_class']}[/dim]")
                if "present_area" in data: 
                    current_values[6] = data["present_area"]
                    self.log(f"[dim][DEBUG] Set AREA to: {data['present_area']}[/dim]")
                if "jiga" in data: 
                    current_values[7] = data["jiga"]
                    self.log(f"[dim][DEBUG] Set JIGA to: {data['jiga']}[/dim]")
                if "jiga_year" in data:
                    current_values[8] = data["jiga_year"]
                    self.log(f"[dim][DEBUG] Set JIGA_YEAR to: {data['jiga_year']}[/dim]")
                if "present_mark1" in data: current_values[9] = data["present_mark1"]
                if "present_mark2" in data: current_values[10] = data["present_mark2"]
                if "present_mark3" in data: current_values[11] = data["present_mark3"]
                if "present_mark_combined" in data: current_values[12] = data["present_mark_combined"]
                
                if "image_status" in data: 
                    current_values[13] = data["image_status"]
                elif "image_path" in data: 
                    current_values[13] = "Y" if data["image_path"] else "N"
                
                self.tree.item(iid, values=current_values)
                self.log(f"[green][DEBUG] Successfully updated tree item {iid}[/green]")
            else:
                self.log(f"[red][DEBUG] Tree item {iid} does NOT exist![/red]")
        except Exception as e:
            self.log(f"[red][ERROR] Error updating row {row}: {e}[/red]")
            import traceback
            self.log(f"[red]{traceback.format_exc()}[/red]")

    def load_excel_data(self):
        file_path = self.excel_file.get()
        if not file_path or not os.path.exists(file_path):
            return
            
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            self.log("파일 내용을 불러오는 중...")
            self.root.update()
            
            handler = ExcelHandler(file_path)
            if handler.open():
                start = self.start_row.get()
                # Read first 100 rows or until empty for preview
                # Or read all rows? Let's read a reasonable amount or all if not too huge
                # For now, let's read up to 1000 rows to be safe
                
                count = 0
                current = start
                
                while True:
                    address = handler.read_address(current)
                    if not address:
                        # Check a few more rows to be sure
                        empty_count = 0
                        for i in range(1, 6):
                            if handler.read_address(current + i):
                                empty_count = 0
                                break
                            empty_count += 1
                        
                        if empty_count >= 5:
                            break
                    
                    if address:
                        excel_id = handler.read_id(current)
                        excel_pnu = handler.read_pnu(current)
                        display_id = excel_id if excel_id else ""
                        display_pnu = excel_pnu if excel_pnu else ""
                        self.tree.insert("", "end", iid=str(current), values=(display_id, address, "", "", display_pnu, "", "", "", "", "", "", "", "", ""))
                        count += 1
                        
                        if not excel_pnu:
                            self.pnu_fetch_queue.put((current, address))
                    
                    current += 1
                    if count >= 1000: # Limit for performance
                        self.log("미리보기는 최대 1000행까지만 표시됩니다.")
                        break
                
                handler.close()
                self.log(f"총 {count}개의 데이터를 불러왔습니다.")
            else:
                self.log("Excel 파일을 열 수 없습니다.")
                messagebox.showerror(
                    "오류", 
                    "엑셀파일 로드시 오류가 발생하였습니다.\n\n양식 다운받기 클릭하여 새로운 파일로 다시 시도 하세요."
                )
                self.excel_file.set("")
                
        except Exception as e:
            self.log(f"데이터 로드 중 오류: {e}")
            messagebox.showerror("오류", f"데이터 로드 실패: {e}")
    
    def log(self, message):
        """Add message to log text area (Thread-safe)."""
        self.root.after(0, lambda: self._log_impl(message))
    
    def _log_impl(self, message):
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
    
    def update_progress(self, row, address, status, message=None):
        """Update progress display (Thread-safe)."""
        self.root.after(0, lambda: self._update_progress_impl(row, address, status, message))
        
    def _update_progress_impl(self, row, address, status, message):
        """Actual progress update implementation."""
        # Update Treeview
        try:
            if self.tree.exists(str(row)):
                current_values = list(self.tree.item(str(row))['values'])
                # (ID, ADDRESS, RESULT, DETAILS, PNU, CLASS, AREA, JIGA, ZONE1, ZONE2, REGULATION, IMAGE)
                
                if status == "processing":
                    current_values[2] = "처리 중"
                elif status == "success":
                    current_values[2] = "성공"
                elif status == "failed":
                    current_values[2] = "실패"
                
                if message:
                    if "|" in message:
                        parts = message.split("|")
                        current_values[3] = parts[0]
                        if len(parts) > 1:
                            current_values[4] = parts[1] # PNU
                    else:
                        current_values[3] = message
                
                tags = ()
                if status == "success": tags = ('success',)
                elif status == "failed": tags = ('failed',)
                
                self.tree.item(str(row), values=current_values, tags=tags)
                
                if status == "processing":
                    self.tree.see(str(row))
                    self.tree.selection_set(str(row))
        except Exception as e:
            print(f"Treeview update error: {e}")

        if status == "processing":
            # Calculate Sequence ID
            start_row = self.start_row.get()
            seq_id = row - start_row + 1
            try:
                if self.tree.exists(str(row)):
                    seq_id = self.tree.item(str(row))['values'][0]
            except Exception:
                pass
            self.progress_var.set(f"{seq_id}번 처리 중: {address}")
        elif status == "success":
            start_row = self.start_row.get()
            seq_id = row - start_row + 1
            try:
                if self.tree.exists(str(row)):
                    seq_id = self.tree.item(str(row))['values'][0]
            except Exception:
                pass
            self.progress_var.set(f"{seq_id}번 완료: {address}")
            self.total_success += 1
        elif status == "failed":
            start_row = self.start_row.get()
            seq_id = row - start_row + 1
            try:
                if self.tree.exists(str(row)):
                    seq_id = self.tree.item(str(row))['values'][0]
            except Exception:
                pass
            self.progress_var.set(f"{seq_id}번 실패: {address}")
            self.total_failed += 1
        
        self.total_processed += 1
        self.update_stats()
        self.root.update_idletasks()
        
    def update_stats(self):
        """Update statistics display."""
        elapsed = 0
        if self.start_time:
            elapsed = time.time() - self.start_time
        
        stats_text = (
            f"처리: {self.total_processed} | "
            f"성공: {self.total_success} | "
            f"실패: {self.total_failed} | "
            f"시간: {elapsed:.1f}s"
        )
        self.stats_label.config(text=stats_text)

    def reset_ui(self):
        """Reset UI elements to their initial state."""
        # Cancel background PNU fetching
        self.fetch_pnu_cancel.set()
        while not self.pnu_fetch_queue.empty():
            try:
                self.pnu_fetch_queue.get_nowait()
            except queue.Empty:
                break
        self.fetch_pnu_cancel.clear()
        
        # Clear Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset Stats
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = None
        self.stats_label.config(text="처리: 0 | 성공: 0 | 실패: 0 | 시간: 0s")
        self.progress_var.set("대기 중...")
        self.progress_bar.stop()
        
        # Clear logs
        if getattr(self, "log_text", None):
            self.log_text.delete(1.0, tk.END)
            
        self.log("초기화 완료. 언제든 새로 시작할 수 있습니다.")
    
    def log_callback(self, message):
        """Callback for crawler log messages."""
        # Convert message to string if it's not already
        if not isinstance(message, str):
            message = str(message)
        
        # Remove rich formatting tags for plain text display
        plain_message = message
        # Remove common rich tags (e.g., [bold], [cyan], [/cyan], etc.)
        import re
        # Remove all rich markup tags
        plain_message = re.sub(r'\[/?[a-z]+\]', '', plain_message)
        plain_message = re.sub(r'\[.*?\]', '', plain_message)
        # Clean up extra whitespace but preserve newlines
        lines = [line.strip() for line in plain_message.split('\n')]
        plain_message = '\n'.join(line for line in lines if line)
        if plain_message:
            self.log(plain_message)
        
    def progress_callback(self, row, address, status, message=None):
        """Callback for crawler progress updates."""
        self.update_progress(row, address, status, message)
    
    def start_crawler(self):
        """Start the crawler in a separate thread."""
        current_text = self.start_btn.cget("text")
        if current_text == "초기화":
            self.log("초기화 버튼 클릭: 모든 데이터를 삭제하고 처음 상태로 되돌립니다.")
            self.excel_file.set("")
            self.reset_ui()
            self.start_btn.config(state=tk.NORMAL, text="시작")
            return

        # Validate file
        if not self.excel_file.get():
            messagebox.showerror("오류", "Excel 파일을 선택해주세요.")
            return
        
        if not os.path.exists(self.excel_file.get()):
            messagebox.showerror("오류", "선택한 파일이 존재하지 않습니다.")
            return
        
        # Reset state
        self.is_running = True
        self.stop_event.clear()
        self.step_event.clear()
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = time.time()
        
        # Update UI
        if self.debug_mode.get():
            self.start_btn.config(text="다음 (Next)", command=self.next_step, state=tk.NORMAL)
            self.log("디버그 모드 시작: '다음' 버튼을 눌러 진행하세요.")
        else:
            self.start_btn.config(state=tk.DISABLED)
            
        self.stop_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
        self.progress_bar.start()
        self.progress_var.set("크롤링 시작 중...")
        self.status_var.set("실행 중")
        self.log_text.delete(1.0, tk.END)
        self.log("크롤링을 시작합니다...")
        self.log(f"파일: {self.excel_file.get()}")
        self.log(f"시작 행: {self.start_row.get()}")
        self.log(f"헤드리스 모드: {self.headless.get()}")
        self.log(f"대기 시간: {self.wait_time.get()}초")
        self.log(f"디버그 모드: {self.debug_mode.get()}")
        self.log("=" * 50)
        
        # Pause background PNU fetching while crawling
        self.fetch_pnu_cancel.set()
        while not self.pnu_fetch_queue.empty():
            try:
                self.pnu_fetch_queue.get_nowait()
            except queue.Empty:
                break
        
        # Set event to trigger background thread loop instead of spinning a new thread
        self.start_crawling_event.set()
    
    def next_step(self):
        """Proceed to next step in debug mode."""
        self.log(">> 다음 단계 진행 요청")
        self.step_event.set()

    def _execute_crawler_job(self):
        """Run crawler job triggered by the persistent crawler thread."""
        try:
            # Map scale text to exactly its underlying value representation
            scale_str = self.scale.get()
            scale = self.scale_options.get(scale_str, "1200") # Default to 1200 if not found

            
            self.log(f"선택된 축적 파싱 결과: {scale} (원본: {scale_str})")

            result = run_crawler(
                file=self.excel_file.get(),
                start_row=self.start_row.get(),
                headless=self.headless.get(),
                wait=self.wait_time.get(),
                verbose=self.verbose.get(),
                scale=scale,
                debug_mode=self.debug_mode.get(),
                save_pdf=self.save_pdf.get(),
                step_event=self.step_event,
                progress_callback=self.progress_callback,
                log_callback=self.log_callback,
                stop_event=self.stop_event,
                data_callback=self.update_data,
                save_request_event=self.save_request_event,
                scraper_instance=self.scraper
            )
            
            # Update UI on completion
            self.root.after(0, self.crawler_completed, result)
            
        except Exception as e:
            self.root.after(0, self.crawler_error, str(e))
    
    def crawler_completed(self, result):
        """Handle crawler completion."""
        self.is_running = False
        self.progress_bar.stop()
        
        # Update final stats
        self.total_processed = result.get("total_processed", 0)
        self.total_success = result.get("total_success", 0)
        self.total_failed = result.get("total_failed", 0)
        self.update_stats()
        
        # Update UI
        self.start_btn.config(text="초기화", command=self.start_crawler, state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.progress_var.set("완료")
        self.status_var.set("완료")
        
        # Re-enable PNU background fetching for any newly missing rows
        self.fetch_pnu_cancel.clear()
        
        # Show completion message
        if result.get("error"):
            messagebox.showerror("오류", f"크롤링 중 오류가 발생했습니다:\n{result['error']}")
        else:
            elapsed = result.get("elapsed_time", 0)
            message = (
                f"크롤링이 완료되었습니다.\n\n"
                f"처리: {self.total_processed}\n"
                f"성공: {self.total_success}\n"
                f"실패: {self.total_failed}\n"
                f"소요 시간: {elapsed:.1f}초"
            )
            messagebox.showinfo("완료", message)
            self.log("=" * 50)
            self.log("크롤링 완료!")
    
    def crawler_error(self, error_msg):
        """Handle crawler error."""
        self.is_running = False
        self.progress_bar.stop()
        self.start_btn.config(text="시작", command=self.start_crawler, state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.progress_var.set("오류 발생")
        self.status_var.set("오류")
        messagebox.showerror("오류", f"크롤링 중 오류가 발생했습니다:\n{error_msg}")
        self.log(f"오류: {error_msg}")
    
    def stop_crawler(self):
        """Stop the crawler."""
        if self.is_running:
            self.stop_event.set()
            self.log("사용자가 중지를 요청했습니다...")
            self.status_var.set("중지 중...")


def main():
    """Main entry point for GUI."""
    import sys
    if sys.platform == "win32":
        try:
            import ctypes
            myappid = f"eumcrawl.crawler.gui.{VERSION}" # Assuming VERSION is defined elsewhere
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # Check Playwright setup (non-blocking)
    root = tk.Tk()
    
    # Set style to dark modern Windows 11 using sv_ttk
    import sv_ttk
    sv_ttk.set_theme("light")
    
    app = CrawlerGUI(root)
    
    # Handle window close
    def on_closing():
        # Save window geometry before closing
        app.save_window_geometry()
        
        
        # Signal background thread to shut down
        app.shutdown_event.set()
        
        if app.is_running:
            if messagebox.askokcancel("종료", "크롤링이 진행 중입니다. 정말 종료하시겠습니까?"):
                app.stop_event.set()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()


if __name__ == "__main__":
    main()

