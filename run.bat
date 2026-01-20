@echo off
setlocal

:: Ensure we are in the script's directory
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [Error] Virtual environment not found.
    echo Please run 'install.bat' to set up the environment.
    pause
    exit /b 1
)

:: Activate virtual environment
call .\venv\Scripts\activate.bat

:: Run the application
echo Starting MIMIC...
python MIMIC.py

:: Check exit code and pause if there was an error
if %errorlevel% neq 0 (
    echo.
    echo [Error] Application crashed or exited with an error.
    pause
)
