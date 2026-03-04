"""Build release package for distribution."""
import os
import shutil
import subprocess
from pathlib import Path

def build_release():
    """Build exe and create distribution package."""
    print("=" * 60)
    print("Building Release Package")
    print("=" * 60)

    # Step 1: Build exe
    print("\n[1/5] Building executable...")
    result = subprocess.run(['pyinstaller', 'crawler.spec'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error building executable:")
        print(result.stderr)
        return False
    print("OK - Executable built successfully")

    # Step 2: Create release folder
    print("\n[2/5] Creating release folder...")
    release_dir = Path('release')
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    print(f"OK - Created {release_dir}")

    # Step 3: Copy exe
    print("\n[3/5] Copying executable...")
    exe_src = Path('dist') / 'crawler.exe'
    exe_dst = release_dir / 'crawler.exe'
    shutil.copy2(exe_src, exe_dst)
    print(f"OK - Copied crawler.exe")

    # Step 4: Copy required files
    print("\n[4/5] Copying required files...")
    files_to_copy = [
        'chromium-win64.zip',  # Browser package
        'example_data.xlsx',   # Example data
        '사용설명서.txt',      # User guide
    ]

    for file in files_to_copy:
        src = Path(file)
        if src.exists():
            dst = release_dir / file
            shutil.copy2(src, dst)
            print(f"OK - Copied {file}")
        else:
            print(f"WARNING - {file} not found, skipping...")

    # Step 5: Create README
    print("\n[5/5] Creating README...")
    readme_content = """부동산 정보 크롤링 프로그램 v1.0
=====================================

실행 방법:
1. crawler.exe와 chromium-win64.zip이 같은 폴더에 있는지 확인
2. 명령 프롬프트(cmd)를 열고 이 폴더로 이동
3. 다음 명령어 실행:
   crawler.exe --file example_data.xlsx

첫 실행 시:
- chromium-win64.zip이 자동으로 압축 해제됩니다 (약 1분 소요)
- browsers 폴더가 생성됩니다
- 이후 실행부터는 바로 시작됩니다

자세한 사용법은 '사용설명서.txt'를 참고하세요.

=======================================
How to Run:
1. Make sure crawler.exe and chromium-win64.zip are in the same folder
2. Open Command Prompt and navigate to this folder
3. Run: crawler.exe --file example_data.xlsx

First time setup:
- chromium-win64.zip will be automatically extracted (~1 minute)
- browsers folder will be created
- Subsequent runs will start immediately

For detailed instructions, see '사용설명서.txt'
"""

    readme_path = release_dir / 'README.txt'
    readme_path.write_text(readme_content, encoding='utf-8')
    print("OK - Created README.txt")

    # Summary
    print("\n" + "=" * 60)
    print("Release package ready!")
    print("=" * 60)
    print(f"\nLocation: {release_dir.absolute()}")
    print("\nContents:")
    for item in release_dir.iterdir():
        size = item.stat().st_size / (1024 * 1024)  # MB
        print(f"  - {item.name} ({size:.1f} MB)")

    print("\n배포 방법:")
    print("1. release 폴더의 모든 파일을 압축 (zip)")
    print("2. 압축 파일을 사용자에게 전달")
    print("3. 사용자는 압축 해제 후 crawler.exe 실행")
    print("\nDistribution:")
    print("1. Compress all files in release folder (zip)")
    print("2. Send the zip file to users")
    print("3. Users extract and run crawler.exe")

    return True

if __name__ == "__main__":
    success = build_release()
    if not success:
        print("\nBuild failed!")
        exit(1)
    print("\nBuild completed successfully!")
