@echo off
chcp 65001 >nul
echo ============================================================
echo Chromium 브라우저 수동 설치 (Manual Chromium Installation)
echo ============================================================
echo.

REM Check if chromium-win64.zip exists
if not exist "chromium-win64.zip" (
    echo 오류: chromium-win64.zip 파일을 찾을 수 없습니다.
    echo Error: chromium-win64.zip file not found.
    echo.
    echo 이 스크립트와 같은 폴더에 chromium-win64.zip 파일을 넣어주세요.
    echo Please place chromium-win64.zip in the same folder as this script.
    echo.
    pause
    exit /b 1
)

echo chromium-win64.zip 파일을 찾았습니다.
echo Found chromium-win64.zip file.
echo.
echo 압축 해제 중... (Extracting...)
echo.

REM Create playwright directory
set "PLAYWRIGHT_DIR=%LOCALAPPDATA%\ms-playwright"
if not exist "%PLAYWRIGHT_DIR%" (
    mkdir "%PLAYWRIGHT_DIR%"
)

REM Extract using PowerShell
powershell -Command "Expand-Archive -Path 'chromium-win64.zip' -DestinationPath '%PLAYWRIGHT_DIR%' -Force"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 오류: 압축 해제에 실패했습니다.
    echo Error: Failed to extract archive.
    echo.
    pause
    exit /b 1
)

REM Rename the extracted folder
cd /d "%PLAYWRIGHT_DIR%"

REM Check what was extracted
if exist "chrome-win" (
    if exist "chromium-1194" (
        rmdir /s /q "chromium-1194"
    )
    move "chrome-win" "chromium-1194"
    echo.
    echo ============================================================
    echo 설치 완료! (Installation Complete!)
    echo ============================================================
    echo.
    echo Chromium이 다음 위치에 설치되었습니다:
    echo Chromium has been installed to:
    echo %PLAYWRIGHT_DIR%\chromium-1194
    echo.
    echo 이제 crawler.exe를 실행할 수 있습니다.
    echo You can now run crawler.exe
    echo.
) else if exist "chromium-win64" (
    if exist "chromium-1194" (
        rmdir /s /q "chromium-1194"
    )
    move "chromium-win64" "chromium-1194"
    echo.
    echo ============================================================
    echo 설치 완료! (Installation Complete!)
    echo ============================================================
    echo.
    echo Chromium이 다음 위치에 설치되었습니다:
    echo Chromium has been installed to:
    echo %PLAYWRIGHT_DIR%\chromium-1194
    echo.
    echo 이제 crawler.exe를 실행할 수 있습니다.
    echo You can now run crawler.exe
    echo.
) else (
    echo.
    echo 경고: 예상된 폴더를 찾을 수 없습니다.
    echo Warning: Expected folder not found.
    echo 압축 해제된 내용을 확인해주세요.
    echo Please check the extracted contents.
    echo.
)

pause
