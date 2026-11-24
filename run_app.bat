@echo off
title Medical Triage & Emergency KBS | IS438
cd /d "%~dp0"
echo Starting Medical Triage Knowledge-Based System...
python -m streamlit run src\app.py --server.port 8501 --theme.primaryColor="#2563eb" --theme.backgroundColor="#ffffff" --theme.secondaryBackgroundColor="#f3f4f6" --theme.textColor="#0f172a"
pause
