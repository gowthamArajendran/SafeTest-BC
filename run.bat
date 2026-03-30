@echo off
echo Setting up Python Virtual Environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing requirements...
pip install -r requirements.txt
echo Starting Application...
python app.py
pause
