@echo off
echo ========================================
echo Starting ResearchLens AI
echo ========================================

if not exist venv (
    echo Virtual environment not found.
    echo Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
streamlit run app.py
pause
