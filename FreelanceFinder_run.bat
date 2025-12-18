@echo off
cd /d "D:\Projects\Tools\FreelanceFinder"

start "" /B "%CD%\.venv\Scripts\pythonw.exe" "%CD%\src\main.py" >> "%CD%\run.log" 2>&1
exit