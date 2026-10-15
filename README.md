# job-finder

A personal daily job digest pipeline. Pulls co-op/intern listings from job APIs, filters them by job title and location (Ontario), deduplicates against a local SQLite store, and emails an HTML digest. Runs on a Windows Task Scheduler cron or manually via a Flask web UI.

## How it works

1. Fetches listings from Adzuna (official API) and Indeed Canada + LinkedIn (via [JobSpy](https://github.com/speedyapply/JobSpy), no key needed) across ~32 hardware-focused search queries (mechanical, robotics, embedded, aerospace, manufacturing, etc.). Each source fails independently.
2. Keeps titles that are both student-level (intern, co-op, new grad…) and hardware/mechanical, in Ontario; drops senior/PhD and software/civil/business roles
3. Drops any listings already seen in previous runs (SQLite dedup)
4. Emails a styled HTML digest via Gmail SMTP, newest postings first

Only new listings trigger an email — if nothing new was found, the run exits silently.

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

**CLI (one-shot):**
```bash
python run.py
```
Logs to `logs/run.log` and stdout. Exit 0 = success, exit 1 = error.

**Web UI:**
```bash
python app.py
```
Opens a Flask UI at `http://localhost:5000` with a button to trigger the pipeline and view live logs.

**Scheduled (Windows Task Scheduler):**
```bat
scheduler\run_daily.bat
```
See `scheduler/SETUP.md` for Task Scheduler configuration. Also logs to `logs/scheduler.log`.

## Project structure

```
run.py                  # Pipeline entry point
config.py               # All constants and search queries — edit this to change what gets searched
db.py                   # SQLite helpers (init, dedup, mark seen)
filters.py              # Job-title + Ontario location filtering
email_sender.py         # Builds and sends HTML digest via Gmail
app.py                  # Flask web UI wrapper
sources/
  adzuna.py             # Adzuna API source
  jobspy_source.py      # Indeed CA + LinkedIn via python-jobspy (pinned; scraper, not an official API)
  __init__.py           # BaseSource ABC
scheduler/
  run_daily.bat         # Task Scheduler wrapper
  SETUP.md              # Scheduler setup instructions
data/                   # SQLite DB lives here (gitignored)
logs/                   # Log files (gitignored)
```

## Adding a new job source

1. Create `sources/<name>.py` implementing `BaseSource` — `name` attribute + `fetch() -> list[dict]`
2. Use source-prefixed IDs: `f"{self.name}:{raw_id}"`
3. Register in `run.py` by adding to the `sources` list in `main()`

## Customizing searches

Edit `SEARCH_QUERIES` and the keyword lists (`STUDENT_KEYWORDS`, `CORE_KEYWORDS`, `DISCIPLINE_KEYWORDS`, `OFF_SCOPE_KEYWORDS`, `EXCLUDE_KEYWORDS`) in `config.py` — the comment above them explains how they combine. `JOBSPY_SITES` controls which sites JobSpy scrapes (drop `"linkedin"` if it rate-limits you). No code changes needed elsewhere.
