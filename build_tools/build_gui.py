"""Build script for creating Windows GUI executable."""

import os
import sys
import shutil
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.resolve()


def check_requirements():
    """Check if all required packages are installed."""
    print("Checking requirements...")
    try:
        import playwright
        import openpyxl
        import click
        import rich
        import PIL
        import requests
        # tkinter is included with Python, but check anyway
        try:
            import tkinter
        except ImportError:
            print("[FAIL] tkinter not available (should be included with Python)")
            return False
        print("[OK] All required packages installed")
        return True
    except ImportError as e:
        print(f"[FAIL] Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        print("Run: pip install -r requirements.txt")
        return False


def get_version():
    """Extract version from src/config.py."""
    try:
        config_path = PROJECT_ROOT / "src" / "config.py"
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("VERSION ="):
                    # Extract version string (e.g., VERSION = "1.2" -> 1.2)
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    return version
        return "1.0" # Default fallback
    except Exception as e:
        print(f"[WARN] Failed to read version from config.py: {e}")
        return "1.0"


def install_playwright_browsers():
    """Install Playwright browsers."""
    print("\nInstalling Playwright browsers...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True
        )
        print("[OK] Playwright browsers installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Failed to install Playwright browsers: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def build_executable():
    """Build GUI executable using PyInstaller."""
    print("\nBuilding GUI executable...")
    try:
        # Clean previous builds in parent directory
        parent_dir = PROJECT_ROOT
        for dir_name in ["build", "dist"]:
            dir_path = parent_dir / dir_name
            if dir_path.exists():
                print(f"Cleaning {dir_path}/...")
                shutil.rmtree(dir_path)

        # Run PyInstaller using Python module (more reliable)
        result = subprocess.run(
            [
                sys.executable, "-m", "PyInstaller", 
                "--distpath", str(parent_dir / "dist"),
                "--workpath", str(parent_dir / "build"),
                "crawler_gui.spec"
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=SCRIPT_DIR
        )
        print("[OK] GUI executable built successfully")

        # Check platform for executable name
        import platform
        version = get_version()
        if platform.system() == "Windows":
            original_name = "crawler_gui.exe"
            exe_name = f"crawler_gui_v{version}.exe"
        else:
            original_name = "crawler_gui"
            exe_name = f"crawler_gui_v{version}"

        # Rename the output file
        # Check potential dist locations (project root or build_tools dir)
        potential_dirs = [
            parent_dir / "dist",
            SCRIPT_DIR / "dist"
        ]
        
        renamed = False
        for dist_dir in potential_dirs:
            original_path = dist_dir / original_name
            exe_path = dist_dir / exe_name
            
            print(f"checking {original_path}")
            if original_path.exists():
                print(f"[INFO] Found executable at: {original_path}")
                if exe_path.exists():
                    try:
                        exe_path.unlink()
                    except PermissionError:
                         print(f"[FAIL] Cannot verify/delete existing file {exe_path}. Is it open?")
                         return False

                try:
                    original_path.rename(exe_path)
                    print(f"[OK] Renamed to {exe_name}")
                    renamed = True
                    break
                except OSError as e:
                    print(f"[FAIL] Error renaming file: {e}")
                    return False
        
        if not renamed:
             # If we didn't find the original, maybe it was already named correctly?
             # Check if target name exists
             found_target = False
             for dist_dir in potential_dirs:
                 if (dist_dir / exe_name).exists():
                     print(f"[INFO] Target file {exe_name} already exists at {dist_dir}")
                     found_target = True
                     break
             
             if not found_target:
                 print(f"[FAIL] Could not find {original_name} in dist folders.")
                 return False

        print(f"[OK] Output: {exe_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Build failed: {e}")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def create_release_package():
    """Create release package with documentation."""
    print("\nCreating release package...")
    try:
        import platform
        
        # Paths relative to project root
        parent_dir = PROJECT_ROOT
        release_dir = parent_dir / "release_gui"
        docs_dir = parent_dir / "docs"
        
        if release_dir.exists():
            shutil.rmtree(release_dir)
        release_dir.mkdir()

        # Copy executable (platform-specific name)
        version = get_version()
        if platform.system() == "Windows":
            exe_name = f"crawler_gui_v{version}.exe"
        else:
            exe_name = f"crawler_gui_v{version}"

        exe_path = parent_dir / "dist" / exe_name
        if exe_path.exists():
            shutil.copy(exe_path, release_dir / exe_name)
            print(f"[OK] Copied {exe_name}")
        else:
            print(f"[FAIL] {exe_name} not found in dist/")

        # Copy documentation from docs/ directory
        doc_files = [
            ("README.txt", docs_dir / "README.txt"),
            ("README.md", parent_dir / "README.md"),
            ("INSTALL_GUIDE.txt", docs_dir / "INSTALL_GUIDE.txt"),
        ]
        
        for dest_name, src_path in doc_files:
            if src_path.exists():
                shutil.copy(src_path, release_dir / dest_name)
                print(f"[OK] Copied {dest_name}")

        # Create example data file if it doesn't exist
        example_data = parent_dir / "example_data.xlsx"
        if example_data.exists():
            shutil.copy(example_data, release_dir / "example_data.xlsx")
            print("[OK] Copied example_data.xlsx")
        else:
            print("[WARN] example_data.xlsx not found (optional)")

        print(f"[OK] Release package created in: {release_dir}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to create release package: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main build process."""
    import platform

    print("="*50)
    print("Real Estate Crawler - GUI Build Script")
    print("="*50)
    print(f"Platform: {platform.system()}")
    print("="*50 + "\n")

    # Check Python version
    if sys.version_info < (3, 11):
        print("[WARN] Warning: Python 3.11+ recommended")

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Install Playwright browsers
    if not install_playwright_browsers():
        print("[WARN] Warning: Playwright browsers not installed")
        print("  Users will need to run: playwright install chromium")

    # Build executable
    if not build_executable():
        sys.exit(1)

    # Create release package
    if not create_release_package():
        print("[WARN] Warning: Release package not created")

    print("\n" + "="*50)
    print("GUI Build completed successfully!")
    print("="*50)

    version = get_version()
    if platform.system() == "Windows":
        exe_name = f"crawler_gui_v{version}.exe"
    else:
        exe_name = f"crawler_gui_v{version}"

    parent_dir = PROJECT_ROOT
    print(f"\n[OK] Built: {parent_dir / 'dist' / exe_name}")
    print(f"[OK] Package: {parent_dir / 'release_gui' / exe_name}\n")

    print("Next steps:")
    print(f"1. Test: {parent_dir / 'dist' / exe_name}")
    print("2. Distribute: release_gui/ folder\n")


if __name__ == "__main__":
    main()
