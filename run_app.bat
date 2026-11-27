@echo off
title AEGIS Medical Triage CDSS | IS438
cd /d "%~dp0"
echo Starting AEGIS Clinical Emergency Triage Decision Support System...

if exist ".venv\Scripts\python.exe" (
    call .venv\Scripts\activate.bat
    python -m streamlit run src\app.py --server.port 8501
) else (
    python -m streamlit run src\app.py --server.port 8501
)
pause
