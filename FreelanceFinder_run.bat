@echo off

cd /d "D:Projects\Tools\FreelanceFinder"

call .venv\Scripts\activate.bat

start "" /B python src\main.py
