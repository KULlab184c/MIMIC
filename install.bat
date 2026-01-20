@echo off
setlocal

echo [Setup] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in your PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo [Setup] Creating virtual environment 'venv'...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)

echo [Setup] Activating virtual environment...
call .\venv\Scripts\activate.bat

echo [Setup] Upgrading pip...
python -m pip install --upgrade pip

echo [Setup] Installing dependencies from requirements.txt...
if exist requirements.txt (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    echo Error: requirements.txt not found!
    pause
    exit /b 1
)

echo.
echo [Setup] Installation successful.
pause
