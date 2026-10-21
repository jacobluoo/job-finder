# Running Job Finder automatically

## How runs are timed
- `scheduler/start_site.bat` starts the website in the background (no window) at http://localhost:5000.
- While the site is running it checks **on startup and then every hour** whether to run the pipeline.
- A run only happens if the last successful run finished **more than 20 hours ago** (`MIN_HOURS_BETWEEN_RUNS` in `config.py`). So logging on several times a day, or leaving the PC on for days, still gives about one run per day — no wasted scrapes, no LinkedIn throttling.
- The **Refresh now** button on the site forces a run whenever you want one.
- Each run saves new jobs to the site and emails you a digest whose links open the site.

So the only thing to set up is: **start the site when you log on.**

## Prerequisites
- Python on your PATH, `pip install -r requirements.txt` done
- `.env` in the project root with your credentials (see README)

## Option A — Startup folder (recommended, no admin needed)
1. Press `Win + R`, type `shell:startup`, press Enter.
2. Right-click in the folder → **New → Shortcut**.
3. Location: the full path to `scheduler\start_site.bat` in this project, e.g.
   `C:\Users\Jacob\Documents\Coding\personal\job_finder\scheduler\start_site.bat`
4. Name it `Job Finder` → **Finish**.

## Option B — Task Scheduler
1. `Win + R` → `taskschd.msc` → **Create Task…** (not "Basic Task").
2. **General**: name `Job Finder`; *Run only when user is logged on*.
3. **Triggers** → New → *At log on* (your user).
4. **Actions** → New → *Start a program* → `scheduler\start_site.bat` (full path); *Start in*: the project folder.
5. **Conditions**: untick *Start the task only if the computer is on AC power* (laptops).
6. **Settings**: untick *Stop the task if it runs longer than…* (the site runs all session).

## Checking it works
- Open http://localhost:5000 — the header shows when the last run happened.
- `logs\run.log` has a line per check, e.g. `Last successful run was 3.2h ago (< 20h) — skipping`.
- `logs\site.log` holds anything the site prints if it crashes.

## Running the pipeline without the site
`scheduler\run_daily.bat` (or `python run.py`) runs once, with the same 20h guard; `python run.py --force` skips the guard. Output goes to `logs\scheduler.log` and `logs\run.log`.

## Stopping the site
It runs as `pythonw.exe`. End it from Task Manager (Details tab → `pythonw.exe`), or:
`taskkill /IM pythonw.exe /F` (this also stops any other pythonw programs you have running).

## Troubleshooting
- **Email links don't open**: the site isn't running — run `scheduler\start_site.bat`.
- **"python is not recognized"**: use the full path to `pythonw.exe` / `python.exe` in the `.bat` files.
- **No email**: check `logs\run.log`; verify `.env` Gmail address + App Password. New jobs are still on the site even if the email fails.
