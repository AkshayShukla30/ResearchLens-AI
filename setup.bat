@echo off
echo ========================================
echo ResearchLens AI Setup
echo ========================================

python -m venv venv
if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

if not exist .env (
    copy .env.example .env
    echo Created .env from .env.example. Add your API key before running.
)

echo.
echo Setup complete.
echo Run: run.bat
pause
