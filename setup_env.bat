@echo off
REM Ouroboros Ops - Automated Windows Environment Setup
REM This script sets up the Python virtual environment and dependencies

echo ============================================================
echo OUROBOROS OPS - ENVIRONMENT SETUP
echo ============================================================

echo.
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo ✅ Python found

echo.
echo Creating virtual environment...
if exist venv (
    echo ⚠️ Virtual environment already exists
    echo Removing existing venv...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment created

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment activated

echo.
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo Make sure requirements.txt exists and is valid
    pause
    exit /b 1
)
echo ✅ Dependencies installed

echo.
echo Running quick validation...
python demo.py --quick
if errorlevel 1 (
    echo ⚠️ Demo script encountered issues (this may be normal)
) else (
    echo ✅ Demo script completed successfully
)

echo.
echo ============================================================
echo 🎉 SETUP COMPLETE!
echo ============================================================
echo.
echo Your Ouroboros Ops environment is ready!
echo.
echo To run the simulation:
echo   python main.py --agents 1000 --grid-size 256
echo.
echo To run benchmarks:
echo   python -m cli.benchmark --quick
echo.
echo To activate the environment in future sessions:
echo   venv\Scripts\activate.bat
echo.
echo For more information, see README.md
echo ============================================================
pause