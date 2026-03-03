@echo off
cd %~dp0

set VENV_ACTIVATE_SCRIPT=.venv\Scripts\activate.bat

IF EXIST %VENV_ACTIVATE_SCRIPT% (
    call %VENV_ACTIVATE_SCRIPT%
    pip install -r requirements.txt > nul
    start "TimeTable" pythonw main.pyw
) ELSE (
    pip install -r requirements.txt > nul
    start "TimeTable" pythonw main.pyw
)
