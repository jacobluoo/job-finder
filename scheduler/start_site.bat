@echo off
rem Starts the Job Finder website in the background (no console window).
rem Register this to run at Windows logon - see scheduler/SETUP.md.
rem The site checks hourly and runs the pipeline when the last run is > 20h old.
cd /d "%~dp0.."
start "" pythonw app.py >> logs\site.log 2>&1
