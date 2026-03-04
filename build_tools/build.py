"""Build script for creating Windows executable."""

import os
import sys
import shutil
import subprocess
from pathlib import Path


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
        print("✓ All required packages installed")
        return True
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        return False


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
        print("✓ Playwright browsers installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Playwright browsers: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def build_executable():
    """Build executable using PyInstaller."""
    print("\nBuilding executable...")
    try:
        # Clean previous builds
        for dir_name in ["build", "dist"]:
            if os.path.exists(dir_name):
                print(f"Cleaning {dir_name}/...")
                shutil.rmtree(dir_name)

        # Run PyInstaller using Python module (more reliable)
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "crawler.spec"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ Executable built successfully")

        # Check platform for executable name
        import platform
        if platform.system() == "Windows":
            exe_name = "crawler.exe"
        else:
            exe_name = "crawler"

        print(f"✓ Output: dist/{exe_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def create_release_package():
    """Create release package with documentation."""
    print("\nCreating release package...")
    try:
        import platform
        release_dir = Path("release")
        if release_dir.exists():
            shutil.rmtree(release_dir)
        release_dir.mkdir()

        # Copy executable (platform-specific name)
        if platform.system() == "Windows":
            exe_name = "crawler.exe"
        else:
            exe_name = "crawler"

        exe_path = Path("dist") / exe_name
        if exe_path.exists():
            shutil.copy(exe_path, release_dir / exe_name)
            print(f"✓ Copied {exe_name}")
        else:
            print(f"⚠ {exe_name} not found in dist/")

        # Copy documentation
        if os.path.exists("README.txt"):
            shutil.copy("README.txt", release_dir / "README.txt")
            print("✓ Copied README.txt")

        if os.path.exists("README.md"):
            shutil.copy("README.md", release_dir / "README.md")
            print("✓ Copied README.md")

        if os.path.exists("INSTALL_GUIDE.txt"):
            shutil.copy("INSTALL_GUIDE.txt", release_dir / "INSTALL_GUIDE.txt")
            print("✓ Copied INSTALL_GUIDE.txt")

        # Create example data file if it doesn't exist
        if os.path.exists("example_data.xlsx"):
            shutil.copy("example_data.xlsx", release_dir / "example_data.xlsx")
            print("✓ Copied example_data.xlsx")
        else:
            print("⚠ example_data.xlsx not found (optional)")

        print(f"✓ Release package created in: {release_dir.absolute()}")
        return True
    except Exception as e:
        print(f"✗ Failed to create release package: {e}")
        return False


def main():
    """Main build process."""
    import platform

    print("="*50)
    print("Real Estate Crawler - Build Script")
    print("="*50)
    print(f"Platform: {platform.system()}")
    print("="*50 + "\n")

    # Show platform limitation
    current_platform = platform.system()
    if current_platform == "Darwin":
        print("⚠  Mac에서는 Mac 실행 파일만 빌드할 수 있습니다.")
        print("⚠  On Mac, only Mac executable can be built.\n")
        print("💡 모든 플랫폼용 빌드가 필요하면:")
        print("💡 For all platforms, use GitHub Actions:\n")
        print("   1. GitHub에 코드 푸시:")
        print("      git add . && git commit -m 'Build' && git push")
        print("   2. https://github.com/YOUR_REPO/actions 방문")
        print("   3. 'Build Executables' workflow 실행")
        print("   4. Artifacts에서 Windows/Mac/Linux 빌드 다운로드\n")
        print("="*50 + "\n")

        response = input("현재 플랫폼(Mac)용만 빌드할까요? (y/n): ")
        if response.lower() != 'y':
            print("빌드 취소됨")
            return
    elif current_platform != "Windows":
        print(f"⚠  {current_platform}에서는 {current_platform} 실행 파일만 빌드됩니다.\n")
        print("💡 Windows EXE가 필요하면 GitHub Actions를 사용하세요.\n")

    # Check Python version
    if sys.version_info < (3, 11):
        print("⚠ Warning: Python 3.11+ recommended")

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Install Playwright browsers
    if not install_playwright_browsers():
        print("⚠ Warning: Playwright browsers not installed")
        print("  Users will need to run: playwright install chromium")

    # Build executable
    if not build_executable():
        sys.exit(1)

    # Create release package
    if not create_release_package():
        print("⚠ Warning: Release package not created")

    print("\n" + "="*50)
    print("Build completed successfully!")
    print("="*50)

    if platform.system() == "Windows":
        exe_name = "crawler.exe"
    else:
        exe_name = "crawler"

    print(f"\n✓ Built: dist/{exe_name}")
    print(f"✓ Package: release/{exe_name}\n")

    print("Next steps:")
    print(f"1. Test: dist/{exe_name} --file example_data.xlsx")
    print("2. Distribute: release/ folder\n")

    if platform.system() != "Windows":
        print("🔔 Windows EXE가 필요하면:")
        print("   python build_all_platforms.py")
        print("   (GitHub Actions를 사용한 자동 빌드)\n")


if __name__ == "__main__":
    main()
