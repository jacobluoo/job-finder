# Plan: Personal Job Listing Aggregator

## Task Description

Build a Python-based daily job aggregator for a second-year Mechanical & Materials + AI Systems Engineering co-op student at Western University. The system fetches new co-op/internship postings from Adzuna (Phase 1), deduplicates them in SQLite, filters for relevance by keyword and location, and sends a clean HTML email digest via Gmail SMTP with App Password. The architecture is modular so RSS feeds and Greenhouse/Lever boards can be added later without touching core logic.

## Objective

A runnable Python project at `C:\Users\Jacob\Documents\Coding\personal\job_finder\` that:
- Fetches job listings from Adzuna daily (country: `ca`, region: Ontario + remote queries)
- Filters for co-op/internship/entry-level roles matching target keywords
- Deduplicates listings so each job appears in the digest exactly once, ever
- Sends an HTML email digest to jacob.rj.luo@gmail.com listing new jobs with title, company, location, salary, link, and date posted
- Can be scheduled via Windows Task Scheduler with a single `.bat` launcher

## Assumptions

- **Phase 1 scope is Adzuna only.** RSS feeds and Greenhouse/Lever are future modules. The plan includes the extension points but does not implement them.
- **Credentials stored in `.env`.** `python-dotenv` loads them at runtime; `.env` is gitignored.
- **Recipient email is `jacob.rj.luo@gmail.com`** (from session context). Configurable via `.env`.
- **Deduplication key is the Adzuna listing `id` field**, prefixed with the source name (e.g., `adzuna:12345678`). This is stable and unique per job per Adzuna's API.
- **No email is sent if zero new listings are found** — avoids empty digest noise.
- **On API failure**, the run logs the error to `logs/run.log` and exits with a non-zero code (Task Scheduler can alert on this). No partial email is sent.
- **Salary display** shows a range if both `salary_min` and `salary_max` are present, one value if only one is present, and "Not listed" if absent. `salary_is_predicted=1` is displayed as "(est.)" suffix.
- **Adzuna country code for Canada is `ca`.** Two searches per run: `where=Ontario` and `where=remote` to capture both.

## Problem Statement

Co-op job hunting requires checking multiple job boards daily, manually filtering noise, and tracking what you've already seen. Without automation, relevant postings get missed or you waste time re-reviewing the same listings. A targeted daily digest surfacing only *new* relevant postings dramatically reduces friction.

## Solution Approach

A lightweight Python CLI pipeline with four cleanly separated concerns:

1. **Sources** — pluggable fetcher modules, each returning a normalized list of job dicts
2. **Filters** — stateless functions that accept a list of jobs and return a filtered list
3. **Database** — SQLite store for seen job IDs; insert-only, no updates needed
4. **Notifier** — HTML email builder and SMTP sender

`run.py` is the thin orchestrator that wires these together. No framework needed — the whole system is ~400 lines across 6 focused files.

## Verified API Patterns

| Library/API | Version Checked | Recommended Pattern | Deprecation Warnings |
|-------------|----------------|--------------------|--------------------|
| Adzuna Jobs REST API | v1 (stable since 2013) | `requests.get("https://api.adzuna.com/v1/api/jobs/ca/search/{page}", params={"app_id":..., "app_key":..., "what":..., "where":..., "results_per_page":50})` — auth via query params, page in URL path, `Accept: application/json` header | XML unsupported — JSON only; no other deprecations |
| python-dotenv | latest | `from dotenv import load_dotenv; load_dotenv()` | none |
| smtplib | stdlib | `smtplib.SMTP_SSL("smtp.gmail.com", 465)` with Gmail App Password | none |

## Relevant Files

### New Files to Create

- `run.py` — Entry point; orchestrates fetch → filter → deduplicate → email pipeline
- `config.py` — Loads `.env` via dotenv; exposes typed config constants and search params
- `db.py` — SQLite wrapper: `init_db()`, `filter_new(jobs)`, `mark_seen(jobs)`
- `filters.py` — `apply_filters(jobs)`: keyword match + location match, returns filtered list
- `sources/__init__.py` — `BaseSource` abstract class with `fetch() -> list[dict]` interface
- `sources/adzuna.py` — Adzuna fetcher implementing `BaseSource`; handles pagination + normalization
- `email_sender.py` — `build_html(jobs)` and `send_digest(jobs)` using smtplib + Gmail SMTP
- `requirements.txt` — `requests`, `python-dotenv`
- `.env.example` — Template with all required env var keys (no values)
- `scheduler/run_daily.bat` — Windows Task Scheduler launcher calling `python run.py`
- `logs/.gitkeep` — Ensures logs directory exists in git
- `data/.gitkeep` — Ensures data directory exists in git
- `.gitignore` — Ignores `.env`, `data/jobs.db`, `logs/*.log`, `__pycache__`

## Implementation Phases

### Phase 1: Foundation
Set up the project scaffold: directory structure, `.gitignore`, `requirements.txt`, `.env.example`, `config.py`, and `db.py`. This phase establishes the data contract (the normalized job dict schema) that all other modules depend on.

### Phase 2: Core Implementation
Implement `sources/adzuna.py` (the fetcher), `filters.py` (keyword + location logic), and `email_sender.py` (HTML digest builder and SMTP sender). Each module is independently testable against the normalized job dict schema.

### Phase 3: Integration & Polish
Wire everything together in `run.py`. Add `scheduler/run_daily.bat` with Task Scheduler setup instructions. Add structured logging to `logs/run.log`. Validate the full end-to-end flow with a live Adzuna API call and a real test email send.

## Team Orchestration

- You operate as the team lead and orchestrate the team to execute the plan.
- You NEVER operate directly on the codebase. Use `Task` and `Task*` tools to deploy team members.
- Builders execute in sequence where there are data contract dependencies (Phase 1 before Phase 2 before Phase 3).
- The validator runs only after all builders complete.

### Team Members

- Builder
  - Name: builder-foundation
  - Role: Set up project structure, config, database layer, and data contracts
  - Agent Type: builder
  - Resume: true

- Builder
  - Name: builder-sources
  - Role: Implement Adzuna source fetcher and filters
  - Agent Type: builder
  - Resume: true

- Builder
  - Name: builder-notifier
  - Role: Implement email_sender.py HTML digest and SMTP logic
  - Agent Type: builder
  - Resume: true

- Builder
  - Name: builder-integration
  - Role: Implement run.py orchestrator, scheduler bat file, and logging
  - Agent Type: builder
  - Resume: true

- Validator
  - Name: validator-e2e
  - Role: Validate acceptance criteria — imports, DB init, filter logic, email formatting
  - Agent Type: validator
  - Resume: false

### Pipeline Determinism Map

| Node | Determinism | Inputs | Output | Can Change? |
|------|------------|--------|--------|-------------|
| Context7 lookup | NON-DETERMINISTIC | API/library names | Current docs/patterns | External state varies |
| Plan creation | NON-DETERMINISTIC | Prompt + research + judgment | Plan document | Already non-deterministic |
| builder-foundation | DETERMINISTIC | Plan document only | Project scaffold + db.py | NO |
| builder-sources | DETERMINISTIC | Plan document + db.py contract | adzuna.py + filters.py | NO |
| builder-notifier | DETERMINISTIC | Plan document + job dict schema | email_sender.py | NO |
| builder-integration | DETERMINISTIC | All prior outputs | run.py + bat + logs | NO |
| validator-e2e | NON-DETERMINISTIC (advisory) | Finished code | Pass/Fail report | Advisory only |

## Step by Step Tasks

### 1. Scaffold Project Foundation
- **Task ID**: foundation
- **Depends On**: none
- **Assigned To**: builder-foundation
- **Agent Type**: builder
- **Parallel**: false
- Create directory structure: `sources/`, `scheduler/`, `logs/`, `data/`
- Write `.gitignore` (excludes `.env`, `data/jobs.db`, `logs/*.log`, `__pycache__`, `*.pyc`)
- Write `requirements.txt`:
  ```
  requests>=2.31.0
  python-dotenv>=1.0.0
  ```
- Write `.env.example`:
  ```
  ADZUNA_APP_ID=your_app_id_here
  ADZUNA_APP_KEY=your_app_key_here
  GMAIL_ADDRESS=your_gmail@gmail.com
  GMAIL_APP_PASSWORD=your_16_char_app_password
  RECIPIENT_EMAIL=jacob.rj.luo@gmail.com
  ```
- Write `config.py` — loads `.env`, exposes:
  ```python
  ADZUNA_APP_ID: str
  ADZUNA_APP_KEY: str
  GMAIL_ADDRESS: str
  GMAIL_APP_PASSWORD: str
  RECIPIENT_EMAIL: str
  SEARCH_QUERIES: list[dict]  # list of {what, where} dicts for Adzuna
  KEYWORDS: list[str]         # filter keywords
  DB_PATH: str                # path to data/jobs.db
  LOG_PATH: str               # path to logs/run.log
  ```
  `SEARCH_QUERIES` should include at minimum:
  ```python
  [
      {"what": "mechanical engineer intern", "where": "Ontario"},
      {"what": "automation engineer co-op", "where": "Ontario"},
      {"what": "robotics intern", "where": "Ontario"},
      {"what": "embedded systems intern", "where": "Ontario"},
      {"what": "mechanical engineer intern", "where": "remote"},
      {"what": "automation engineer intern", "where": "remote"},
  ]
  ```
  `KEYWORDS` for post-fetch filtering (any match → keep):
  ```python
  ["mechanical", "automation", "robotics", "manufacturing", "embedded",
   "cad", "solidworks", "mechatronics", "intern", "co-op", "coop",
   "co op", "entry level", "junior", "student"]
  ```
- Write `db.py` with:
  - `init_db(db_path)` — creates `jobs` table if not exists:
    ```sql
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        title TEXT,
        company TEXT,
        location TEXT,
        salary_min REAL,
        salary_max REAL,
        salary_is_predicted INTEGER DEFAULT 0,
        url TEXT,
        date_posted TEXT,
        first_seen TEXT NOT NULL
    )
    ```
  - `filter_new(jobs: list[dict], db_path: str) -> list[dict]` — returns only jobs whose `id` is not already in the DB
  - `mark_seen(jobs: list[dict], db_path: str)` — bulk-inserts new jobs; uses `INSERT OR IGNORE`
- Create `logs/.gitkeep` and `data/.gitkeep`

### 2. Implement Sources and Filters
- **Task ID**: sources-filters
- **Depends On**: foundation
- **Assigned To**: builder-sources
- **Agent Type**: builder
- **Parallel**: false
- Write `sources/__init__.py` — defines `BaseSource` ABC:
  ```python
  from abc import ABC, abstractmethod

  class BaseSource(ABC):
      name: str  # used as id prefix, e.g. "adzuna"

      @abstractmethod
      def fetch(self) -> list[dict]:
          """Return list of normalized job dicts."""
          ...
  ```
  Normalized job dict schema:
  ```python
  {
      "id": str,           # "{source_name}:{listing_id}"
      "source": str,       # source name
      "title": str,
      "company": str,
      "location": str,
      "salary_min": float | None,
      "salary_max": float | None,
      "salary_is_predicted": bool,
      "url": str,
      "date_posted": str,  # ISO 8601
  }
  ```
- Write `sources/adzuna.py` implementing `BaseSource`:
  - Constructor reads `config.ADZUNA_APP_ID`, `config.ADZUNA_APP_KEY`, `config.SEARCH_QUERIES`
  - `fetch()` iterates over `SEARCH_QUERIES`, calls `_fetch_query(what, where)` for each, deduplicates by `id` across queries, returns combined list
  - `_fetch_query(what, where)` paginates through all pages (up to page 5 max to avoid hammering API), normalizes each result using field mapping from Verified API Patterns:
    - `id` = `"adzuna:" + result["id"]`
    - `company` = `result.get("company", {}).get("display_name", "Unknown")`
    - `location` = `result.get("location", {}).get("display_name", "Unknown")`
    - `url` = `result.get("redirect_url", "")`
    - `date_posted` = `result.get("created", "")`
  - Implement exponential backoff (1s, 2s, 4s) on HTTP 429 or 5xx responses
  - Set `Accept: application/json` header on all requests
  - Set `max_days_old=1` param to only fetch listings from the last 24 hours (key for "new only" filtering — in addition to DB dedup)
- Write `filters.py`:
  - `apply_filters(jobs: list[dict]) -> list[dict]`
  - Keyword filter: lowercase match of any keyword from `config.KEYWORDS` against `title + company + location` concatenation
  - Location filter: job `location` contains "Ontario", "ON", "Remote", "remote", "Canada" OR `where` param was "remote" (Adzuna results from remote queries are already pre-filtered by the query)
  - Return jobs that pass BOTH filters (keyword AND location)

### 3. Implement Email Notifier
- **Task ID**: notifier
- **Depends On**: foundation
- **Assigned To**: builder-notifier
- **Agent Type**: builder
- **Parallel**: true
- Write `email_sender.py` with two functions:
  - `build_html(jobs: list[dict]) -> str` — returns a complete HTML email string:
    - Inline CSS only (Gmail strips `<style>` blocks)
    - Clean table with columns: **Job Title** (hyperlinked to URL), **Company**, **Location**, **Salary**, **Posted**
    - Header row with dark background (`#1a1a2e`), white text
    - Alternating row colors: white / `#f8f9fa`
    - Salary cell: display `$X – $Y/yr` if both min/max present, `$X/yr` if one, `Not listed` if neither; append ` (est.)` if `salary_is_predicted`
    - Date posted: format ISO string to `MMM DD, YYYY`
    - Subject line prefix: `[Job Digest] {len(jobs)} new listing(s) — {date}`
    - Footer: "Powered by job_finder · {date}"
  - `send_digest(jobs: list[dict])`:
    - Build `MIMEMultipart("alternative")` with plain-text fallback and HTML part
    - Plain-text fallback: simple list of `title @ company — url`
    - Connect to `smtp.gmail.com:465` via `smtplib.SMTP_SSL`
    - Login with `config.GMAIL_ADDRESS` and `config.GMAIL_APP_PASSWORD`
    - Send to `config.RECIPIENT_EMAIL`
    - Raise exceptions — do not swallow; caller (`run.py`) handles logging

### 4. Implement Orchestrator and Scheduler
- **Task ID**: integration
- **Depends On**: sources-filters, notifier
- **Assigned To**: builder-integration
- **Agent Type**: builder
- **Parallel**: false
- Write `run.py`:
  ```python
  # Pipeline: fetch → filter → deduplicate → email
  ```
  Steps:
  1. Configure `logging` to write to `config.LOG_PATH` (append mode) and stdout, format: `%(asctime)s %(levelname)s %(message)s`
  2. `db.init_db(config.DB_PATH)`
  3. Instantiate sources: `[AdzunaSource()]`
  4. For each source, call `source.fetch()`, accumulate all jobs
  5. Apply `filters.apply_filters(all_jobs)`
  6. `new_jobs = db.filter_new(filtered_jobs, config.DB_PATH)`
  7. If `len(new_jobs) == 0`: log "No new listings found", exit 0
  8. `db.mark_seen(new_jobs, config.DB_PATH)`
  9. `email_sender.send_digest(new_jobs)`
  10. Log `f"Digest sent: {len(new_jobs)} new listings"`
  - Wrap entire pipeline in try/except; on exception: log error with traceback, exit 1
- Write `scheduler/run_daily.bat`:
  ```bat
  @echo off
  cd /d C:\Users\Jacob\Documents\Coding\personal\job_finder
  python run.py >> logs\scheduler.log 2>&1
  ```
- Add a `scheduler/SETUP.md` with step-by-step Windows Task Scheduler instructions:
  1. Open Task Scheduler → Create Basic Task
  2. Name: "Job Finder Daily Digest"
  3. Trigger: Daily at preferred time (e.g., 8:00 AM)
  4. Action: Start a program → Browse to `run_daily.bat`
  5. "Run whether user is logged on or not" — check "Run with highest privileges"
  6. Configure for: Windows 10/11

### 5. Validate End-to-End
- **Task ID**: validate-all
- **Depends On**: foundation, sources-filters, notifier, integration
- **Assigned To**: validator-e2e
- **Agent Type**: validator
- **Parallel**: false
- Verify all files exist per the Relevant Files list
- Check `import` chains: `run.py` → `config`, `db`, `filters`, `sources.adzuna`, `email_sender` — no circular imports
- Verify `db.py` `init_db` creates the schema correctly by inspecting the SQL
- Verify `sources/adzuna.py` normalizes all 9 fields of the job dict schema
- Verify `filters.py` handles edge cases: empty list input, job with no title, job with location `None`
- Verify `email_sender.py` `build_html` produces valid HTML with a `<table>` element
- Verify `run.py` exits 0 when no new jobs and does NOT send email
- Verify `.env.example` contains all keys referenced in `config.py`
- Verify `requirements.txt` lists `requests` and `python-dotenv`
- Check `.gitignore` excludes `.env` and `data/jobs.db`

## Acceptance Criteria

1. `python run.py` runs without error given a valid `.env` file
2. On first run, all matching jobs from the last 24 hours are inserted into `data/jobs.db` and a digest email is sent
3. On second run (same day), no email is sent (all jobs already seen)
4. Email renders as a table with correct columns: Job Title (linked), Company, Location, Salary, Posted
5. Salary shows "Not listed" when absent and "(est.)" suffix when predicted
6. Adding a new source requires only: (a) creating `sources/new_source.py` implementing `BaseSource`, (b) adding it to the sources list in `run.py` — no other files change
7. Credentials are never hardcoded — all loaded from `.env`
8. `logs/run.log` captures run outcome (success with count, or error with traceback)
9. `scheduler/run_daily.bat` exists and references the correct project directory

## Validation Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Verify imports work (no credentials needed)
python -c "import config; import db; import filters; from sources.adzuna import AdzunaSource; import email_sender; print('All imports OK')"

# Initialize DB (no credentials needed)
python -c "import config, db; db.init_db(config.DB_PATH); print('DB init OK')"

# Check DB schema
python -c "import sqlite3, config; conn = sqlite3.connect(config.DB_PATH); print(conn.execute(\"SELECT sql FROM sqlite_master WHERE name='jobs'\").fetchone())"

# Dry-run filter with mock data
python -c "
import filters
mock = [{'id':'x','source':'test','title':'Mechanical Engineer Intern','company':'ACME','location':'Ontario, ON','salary_min':None,'salary_max':None,'salary_is_predicted':False,'url':'http://example.com','date_posted':'2026-05-25T00:00:00Z'}]
result = filters.apply_filters(mock)
assert len(result) == 1, 'Filter should pass mechanical engineer intern in Ontario'
print('Filter test passed')
"

# Verify HTML email builds (no SMTP call)
python -c "
import email_sender
mock = [{'title':'Test Intern','company':'ACME','location':'Ontario','salary_min':50000,'salary_max':70000,'salary_is_predicted':False,'url':'http://example.com','date_posted':'2026-05-25T00:00:00Z'}]
html = email_sender.build_html(mock)
assert '<table' in html
assert 'Test Intern' in html
print('HTML build test passed')
"
```

## Notes

- **Adzuna credentials**: Register at https://developer.adzuna.com — free tier allows ~250 requests/day. Each run makes ~6–12 requests (one per query × pagination). Well within limits.
- **Gmail App Password**: Requires 2FA enabled on Google account. Generate at https://myaccount.google.com/apppasswords — select "Mail" + "Windows Computer". Store the 16-char password in `.env`.
- **`max_days_old=1` Adzuna param**: Combined with SQLite deduplication, this is belt-and-suspenders — even if the API returns a listing older than 24h, the DB prevents re-notifying.
- **Future sources**: RSS feeds (e.g., Indeed RSS, WaterlooWorks RSS) follow the same `BaseSource` interface — `fetch()` returns normalized dicts. Greenhouse/Lever require scraping their `/jobs` JSON endpoints per company. Both are ~50-line additions.
- **No pytest required for this phase**: The validation commands use inline Python assertions. A proper test suite can be added in a future phase.
- **Windows Task Scheduler note**: The `.bat` file must use absolute paths because Task Scheduler does not inherit the user's PATH or working directory by default.
