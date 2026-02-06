@echo off
REM Little Cat - Setup and Launch Script for Windows
REM This script helps you quickly set up and run the game

setlocal enabledelayedexpansion

echo.
echo ====================================
echo  LITTLE CAT - AI PET GAME
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    echo Please run this script from the littleCat project directory
    echo.
    pause
    exit /b 1
)

echo [OK] Project files found
echo.

REM Menu
:menu
echo ====================================
echo  CHOOSE AN OPTION:
echo ====================================
echo.
echo 1) Install Dependencies
echo 2) Run Game
echo 3) Run Training Script
echo 4) Run System Test
echo 5) View Documentation
echo 6) Exit
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto game
if "%choice%"=="3" goto trainer
if "%choice%"=="4" goto test
if "%choice%"=="5" goto docs
if "%choice%"=="6" goto end
goto menu

:install
echo.
echo Installing dependencies...
echo This may take a few minutes...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    goto menu
)
echo.
echo [OK] Dependencies installed successfully!
echo.
pause
goto menu

:game
echo.
echo Starting Little Cat Game...
echo.
python src/game.py
if errorlevel 1 (
    echo ERROR: Game failed to start
    echo Make sure all dependencies are installed: python install
    pause
)
goto menu

:trainer
echo.
echo Starting Training Script...
echo This demonstrates the AI learning system
echo.
python src/trainer.py
if errorlevel 1 (
    echo ERROR: Trainer failed to start
    echo Make sure all dependencies are installed: python install
    pause
)
goto menu

:test
echo.
echo Running System Test...
echo.
python test_system.py
if errorlevel 1 (
    echo ERROR: System test failed
    pause
)
echo.
pause
goto menu

:docs
echo.
echo ====================================
echo  DOCUMENTATION FILES
echo ====================================
echo.
echo README.md          - Full feature documentation
echo QUICKSTART.txt     - Quick start guide (START HERE!)
echo ARCHITECTURE.md    - Detailed AI system explanation
echo DIAGRAMS.md        - Visual system diagrams
echo PROJECT_SUMMARY.md - Project overview
echo.
echo Open any of these with a text editor or markdown viewer
echo.
pause
goto menu

:end
echo.
echo Thanks for playing Little Cat!
echo Goodbye!
echo.
exit /b 0
