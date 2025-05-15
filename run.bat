@echo off

REM Activate the virtual environment
call E:\Langfuse\template\capstone-project-2025-s1-team-19\.venv\Scripts\activate.bat

REM Set the Python path to src so modules like 'base' can be found
set PYTHONPATH=E:\Langfuse\template\capstone-project-2025-s1-team-19\src

REM Change directory to where manage.py is located
cd /d E:\Langfuse\template\capstone-project-2025-s1-team-19\src\faultless\mysite

REM Run the Django development server
python manage.py runserver

pause
