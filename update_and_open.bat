@echo off
chcp 65001 >nul
title Taiwan Stock Scanner
cd /d "%~dp0"

echo ================================================
echo  Taiwan Stock Scanner
echo ================================================
echo.
echo [1/3] Updating data (takes ~10 mins)...
echo       Downloading ~1967 stocks in 40 batches.
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found. Please run setup first:
    echo         python -m venv venv
    echo         venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

venv\Scripts\python update_data.py
if errorlevel 1 (
    echo.
    echo [ERROR] Update failed. Check the messages above.
    pause
    exit /b 1
)

echo.
echo [2/3] Pushing to GitHub...
git add uptrend_results.json
git commit -m "update data"
git push
if errorlevel 1 (
    echo.
    echo [WARNING] GitHub push failed, but local data is updated.
)

echo.
echo [3/3] Opening browser...
start "" "https://scan-tw.streamlit.app/"

echo.
echo ================================================
echo  Done! Browser opened.
echo  Press any key to close this window.
echo ================================================
pause
