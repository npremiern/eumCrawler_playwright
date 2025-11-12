@echo off
chcp 65001 >nul
echo ============================================================
echo Chromium 브라우저 설치 (Installing Chromium Browser)
echo ============================================================
echo.
echo 크롤러 실행에 필요한 Chromium 브라우저를 설치합니다.
echo This will install Chromium browser required for the crawler.
echo.
echo 크기: 약 200MB / Size: ~200MB
echo 소요 시간: 3-5분 / Time: 3-5 minutes
echo.
echo ============================================================
echo.

REM Try with Python first
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python을 사용하여 설치합니다...
    echo Installing using Python...
    python -m playwright install chromium
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ============================================================
        echo 설치 완료! (Installation Complete!)
        echo ============================================================
        echo.
        echo 이제 crawler.exe를 실행할 수 있습니다.
        echo You can now run crawler.exe
        echo.
        pause
        exit /b 0
    )
)

REM Try with standalone playwright
where playwright >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Playwright CLI를 사용하여 설치합니다...
    echo Installing using Playwright CLI...
    playwright install chromium
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ============================================================
        echo 설치 완료! (Installation Complete!)
        echo ============================================================
        echo.
        echo 이제 crawler.exe를 실행할 수 있습니다.
        echo You can now run crawler.exe
        echo.
        pause
        exit /b 0
    )
)

echo.
echo ============================================================
echo 자동 설치 실패 (Automatic Installation Failed)
echo ============================================================
echo.
echo Python이 설치되어 있지 않습니다.
echo Python is not installed.
echo.
echo 해결 방법 (Solution):
echo 1. Python 설치: https://www.python.org/downloads/
echo 2. Playwright 설치: pip install playwright
echo 3. 브라우저 설치: python -m playwright install chromium
echo.
echo 또는 zip 파일에 포함된 chromium-win64.zip을 사용하세요.
echo Or use the chromium-win64.zip included in the package.
echo.
pause
exit /b 1
