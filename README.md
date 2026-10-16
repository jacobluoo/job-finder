# job-finder

A personal daily job digest pipeline. Pulls co-op/intern listings from job APIs, filters them by job title and location (Ontario), stores them in a local SQLite database, and shows them on a local website (Flask) where you track each job: viewed, applied (and where), interview, offer, rejected, ghosted. A daily email digest links back to the site. Runs on your own machine — nothing is deployed.

## How it works

1. Fetches listings from Adzuna (official API) and Indeed Canada + LinkedIn (via [JobSpy](https://github.com/speedyapply/JobSpy), no key needed) across ~32 hardware-focused search queries (mechanical, robotics, embedded, aerospace, manufacturing, etc.). Each source fails independently.
2. Keeps titles that are both student-level (intern, co-op, new grad…) and hardware/mechanical, in Ontario; drops senior/PhD and software/civil/business roles
3. Drops any listings already seen in previous runs (SQLite dedup) and saves the new ones
4. Emails a digest of the new ones (newest first) via Gmail SMTP; every link opens the local site

Only new listings trigger an email. A run is skipped if the last successful one was under 20 hours ago (`MIN_HOURS_BETWEEN_RUNS`), so it runs about once a day no matter how often it's triggered.

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Create a `.env` file at the project root**
```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
RECIPIENT_EMAIL=you@gmail.com
```

`GMAIL_APP_PASSWORD` must be a [Gmail App Password](https://support.google.com/accounts/answer/185833) (16 chars), not your account password. Get Adzuna credentials at [developer.adzuna.com](https://developer.adzuna.com).

## Running

**Website (the normal way):**
```bash
python app.py          # or scheduler\start_site.bat to run it in the background
```
Open http://localhost:5000. Tabs: **New**, **Viewed**, **Applied** (applied / interview / offer), **Closed** (rejected / ghosted / withdrawn), **Hidden**, **All**, plus search.
- Clicking a job opens the posting and marks it **viewed**.
- Click a job's **status** to move it to the next one: new → viewed → applied → interview → offer → rejected (then back to new).
- A job's **Details** page shows its timeline and lets you set any status with a note, including ghosted / withdrawn, and where you applied (company site, LinkedIn, Indeed…).
- **Hide** removes jobs you don't want from the list.
- **Refresh now** runs the pipeline immediately and shows the log as it goes.

While running, the site checks hourly and runs the pipeline when the last run is over 20h old. To have it start when you log on, see `scheduler/SETUP.md`.

**CLI (one-shot):**
```bash
python run.py          # skipped if the last run was < 20h ago
python run.py --force  # run anyway
```
Logs to `logs/run.log` and stdout. Exit 0 = success, exit 1 = error.

**Tests:**
```bash
python test_filters.py && python test_app.py
```

## Project structure

```
run.py                  # Pipeline entry point
config.py               # All constants and search queries — edit this to change what gets searched
db.py                   # SQLite: jobs + status tracking, status timeline, run history
filters.py              # Job-title + Ontario location filtering
email_sender.py         # Builds and sends HTML digest via Gmail
app.py                  # Flask website: job list, tracking, refresh, hourly run check
templates/              # base.html, index.html (list), job.html (detail + timeline)
sources/
  adzuna.py             # Adzuna API source
  jobspy_source.py      # Indeed CA + LinkedIn via python-jobspy (pinned; scraper, not an official API)
  __init__.py           # BaseSource ABC
scheduler/
  start_site.bat        # Starts the website in the background (use at logon)
  run_daily.bat         # Runs the pipeline once (CLI fallback)
  SETUP.md              # Start-at-logon instructions
data/                   # SQLite DB lives here (gitignored)
logs/                   # Log files (gitignored)
```

## Adding a new job source

1. Create `sources/<name>.py` implementing `BaseSource` — `name` attribute + `fetch() -> list[dict]`
2. Use source-prefixed IDs: `f"{self.name}:{raw_id}"`
3. Register in `run.py` by adding to the `sources` list in `main()`

## Customizing searches

Edit `SEARCH_QUERIES` and the keyword lists (`STUDENT_KEYWORDS`, `CORE_KEYWORDS`, `DISCIPLINE_KEYWORDS`, `OFF_SCOPE_KEYWORDS`, `EXCLUDE_KEYWORDS`) in `config.py` — the comment above them explains how they combine. `JOBSPY_SITES` controls which sites JobSpy scrapes (drop `"linkedin"` if it rate-limits you). No code changes needed elsewhere.
