@echo off
rem Runs the pipeline once. Skips itself if the last successful run was < 20h ago
rem (pass --force to override). Normally the website triggers runs instead.
cd /d "%~dp0.."
python run.py %* >> logs\scheduler.log 2>&1
