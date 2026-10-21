# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal job finder that runs **only on the user's own Windows machine** (never deployed). It scrapes hardware/mechanical engineering co-op/intern listings in Ontario, stores them in SQLite, and serves a local Flask website (http://localhost:5000) where the user tracks each job (viewed → applied → interview → offer → rejected…). A digest email after each run is a nudge whose links all open the local site.

## Running

```bash
python app.py              # the website (normal way); or scheduler\start_site.bat for background (pythonw, no window)
python run.py              # one pipeline run; skipped if the last successful run was < 20h ago
python run.py --force      # run regardless of the 20h guard
python test_filters.py && python test_app.py   # tests (plain asserts, no pytest)
```

`logs/run.log` gets pipeline output; `logs/site.log` gets anything the background site prints; `logs/scheduler.log` gets `run_daily.bat` output.

**A real run takes ~6 minutes** (JobSpy scrapes Indeed + LinkedIn with deliberate delays) **and sends a real email.** Don't trigger one (`run.py --force`, the site's "Refresh now", `POST /run`) to test changes — `test_app.py` stubs the sources and email. LinkedIn throttles bursts with HTTP 429, so back-to-back runs also lose results.

## Environment setup

`.env` at the project root:
```
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=
RECIPIENT_EMAIL=
SITE_URL=            # optional, defaults to http://localhost:5000 (used in email links)
```

`GMAIL_APP_PASSWORD` must be a Gmail App Password (16-char). `RECIPIENT_EMAIL` defaults to `jacob.rj.luo@gmail.com`. Adzuna keys are set (without them that source logs an error and returns nothing); JobSpy needs no key.

`pip install -r requirements.txt` (`python-jobspy` is pinned). On this machine use **Python 3.12** — it's first on PATH, so `python` / `pythonw` (and the `.bat` files) resolve to it; the 3.14 install has no `jobspy`.

## Architecture

```
app.py                  # Flask site: list/tabs/day pages, /go redirect, status updates, Refresh, hourly run check
run.py                  # Pipeline: guard → fetch → filter → dedup → save → email; records each run
config.py               # All constants + keyword lists; loaded from .env at import time
db.py                   # SQLite: jobs (+ tracking columns), status_events, runs; helpers for site + pipeline
filters.py              # apply_filters → _keyword_match + _location_match + _exclude_match (title-based)
email_sender.py         # build_html + send_digest; also posted_key / posted_day / safe_url / site_link used by app.py
templates/              # base.html (layout + CSS), index.html (list), job.html (detail + timeline)
sources/
  __init__.py           # BaseSource ABC — all sources must implement fetch()
  adzuna.py             # AdzunaSource (official API)
  jobspy_source.py      # JobSpySource — Indeed CA + LinkedIn via python-jobspy (scraper)
scheduler/
  start_site.bat        # Starts the site in the background — meant for Windows logon (see SETUP.md)
  run_daily.bat         # One pipeline run (CLI fallback); uses %~dp0 so it works from any cwd
data/jobs.db            # SQLite store (gitignored, auto-created)
```

### Pipeline flow (`run.main(force=False)`)
1. `db.init_db` — creates tables; adds missing `jobs` columns in place via `PRAGMA table_info` + `ALTER TABLE` (keeps existing rows)
2. Skip if `db.run_in_progress()` (a `running` row < 2h old), or — unless `force` — if `db.hours_since_last_success() < config.MIN_HOURS_BETWEEN_RUNS` (20)
3. `db.start_run` → a `_ListHandler` on the root logger captures this run's lines (`run.current_log`, read live by `/run/status`)
4. Each source's `.fetch()` (each fails independently) → `filters.apply_filters` → `db.filter_new`
5. `db.mark_seen` saves new jobs **before** emailing — the site is the record; an email failure is logged but loses nothing and the run still counts as `ok`
6. `email_sender.send_digest` (newest first) if anything is new
7. `db.finish_run` stores status, counts and the captured log

### When runs happen
Only one rule: the 20h guard in `run.main`. Triggers: the site checks at startup and hourly (`_hourly_checker` thread in `app.py`, started only under `__main__`), the "Refresh now" button (forced), and `run.py` / `run_daily.bat`. The intended setup is a Startup-folder shortcut (or logon task) to `start_site.bat`; there is no separate daily scheduled task. `app._run_lock` prevents two runs in the site process; the `runs` table guards across processes.

### Website (`app.py`)
- `GET /` — params `view` (tab), `q` (search over title/company/location), `day` (`YYYY-MM-DD` or `none`). Jobs are grouped **one page per posting day** (`posted_day`), newest day first; a bad/missing `day` falls back to the newest. Tabs come from `db.VIEWS`.
- `GET /go/<id>` — `db.mark_viewed` (only `new → viewed`, never downgrades) then redirects to the posting via `safe_url` (non-http(s) URLs go to the detail page instead). All posting links on the site use this so views are tracked.
- `POST /jobs/<id>/cycle` — status badge click; steps through `db.STATUS_CYCLE` (new → viewed → applied → interview → offer → rejected → new) and returns JSON. Statuses outside the cycle (ghosted, withdrawn, hidden) → next click goes to `new`.
- `GET /jobs/<id>` + `POST /jobs/<id>/status` — detail page form: any status, note, `applied_via`, `application_url` (http(s) only). `next` redirects must be local paths (`/…`, not `//…`).
- `POST /run` (202 / 409 if running), `GET /run/status` (`running`, last `run` row, `log` — live while running).
- werkzeug request logging is set to WARNING so it stays out of `run.log` and the live run log.

### Database (`db.py`)
- `jobs`: original columns + `status` (default `new`), `viewed_at`, `applied_at`, `applied_via`, `application_url`, `updated_at`. `set_status` uses `COALESCE` so blank fields (e.g. a one-click "applied") keep previously saved `applied_via` / `application_url`.
- `status_events(job_id, status, note, created_at)` — per-job timeline; every status change appends one.
- `runs(started_at, finished_at, status running|ok|failed, fetched, filtered, new_count, log)`.
- Statuses: `db.STATUSES`; tab mapping: `db.VIEWS` (applied tab = applied/interview/offer; closed = rejected/ghosted/withdrawn).

### Email (`email_sender.py`)
Every link points at the site, never the posting: `site_link(job)` → `SITE_URL/?view=new&day=<posted_day>#job-<quoted id>`; the list rows have matching `id="job-{{ job.id | urlencode }}"`. Inline CSS only (Gmail strips `<style>`); `_escape()` HTML-escapes all job fields.

## Normalized job dict contract

| Key | Type | Notes |
|-----|------|-------|
| `id` | str | Source-prefixed, e.g. `"adzuna:12345"`, `"jobspy:li-4469608337"` |
| `source` | str | |
| `title` | str | The only field the keyword filters look at |
| `company` | str | |
| `location` | str | e.g. `"Toronto, ON, Canada"` |
| `area` | list[str] | Adzuna's geographic hierarchy (contains the province); `[]` for JobSpy |
| `salary_min` / `salary_max` | float\|None | |
| `salary_is_predicted` | bool | |
| `url` | str | Posting URL |
| `date_posted` | str | ISO 8601 date or datetime (JobSpy gives `YYYY-MM-DD`, Adzuna a UTC timestamp) |

## Adding a new source

1. Create `sources/<name>.py` implementing `BaseSource` — `name` attribute + `fetch() -> list[dict]`
2. Source-prefixed IDs: `f"{self.name}:{raw_id}"`
3. Fill `area` if the API provides a location hierarchy, else `[]`
4. New credentials go in `.env` and `config.py`
5. Register in the `sources` list in `run.main()` (and stub it in `test_app.py`)

## Search scope and filters (`config.py`, `filters.py`)

**Scope:** hardware/mechanical engineering student and entry-level roles, **anywhere in Ontario** (plus anything labelled remote). Software/AI/data, civil/environmental and business roles are intentionally out of scope.

All keyword matching is on the **title only**, **whole words/phrases, case-insensitive** (`filters._pattern`: no letter/digit allowed on either side — so `intern` ≠ `internal`, `lead` ≠ `leadership`, punctuation like `Intern,` still matches). A job passes when:
1. title has a `STUDENT_KEYWORDS` term (intern, co-op, PEY, student, new grad, junior/jr, trainee, EIT, French `stage`/`stagiaire`…), **and**
2. title has a `CORE_KEYWORDS` term (mechanical, robotics, embedded, firmware, hardware, electrical, aerospace, manufacturing, CAD/PLC/FPGA tools…) — always in scope even next to "software" — **or** a `DISCIPLINE_KEYWORDS` term (engineer/engineering, automation, quality, validation, R&D, lean, test…) with **no** `OFF_SCOPE_KEYWORDS` term (software, data, cloud, IT, civil, environmental, water, finance, business…), **and**
3. title has no `EXCLUDE_KEYWORDS` term (senior/lead/manager…, PhD, robotic process automation, test automation, EHS / health & safety), **and**
4. location (`location` + `area`) matches `ontario`, `on`, `greater toronto area` or `remote`.

When changing filters, re-check real listings rather than guessing — titles that slipped through before included Interac/AmEx business internships, RPA (software) roles, and civil/water co-ops; titles that were wrongly dropped included `Intern, Engineering - …` (comma) and trainee/EIT roles. Add cases to `test_filters.py`.

`SEARCH_QUERIES` (what/where pairs, mostly `where="Toronto"`, a few `remote`) drive both Adzuna and JobSpy. JobSpy settings: `JOBSPY_SITES`, `JOBSPY_RESULTS_WANTED` (25), `JOBSPY_HOURS_OLD` (72), `JOBSPY_DELAY_SECONDS` (3).

## Key implementation details

- `config.py` uses `Path(__file__).parent` for `DB_PATH` / `LOG_PATH` — the site/scheduler may start with a different cwd.
- `db.filter_new` / `db.mark_seen` guard `if not jobs: return` (avoids `WHERE id IN ()`).
- `test_app.py` points `config.DB_PATH` / `LOG_PATH` at a temp dir **before** importing `db` / `run` / `app` (app.py calls `init_db` at import) — keep that order.
- Restarting the background site: stop the `pythonw.exe … app.py` processes, wait a second (the old process holds `logs/site.log`, and `start_site.bat`'s redirect fails if it's still locked), then run `start_site.bat`. Startup takes a few seconds (JobSpy import).
- Adzuna retries HTTP 429/5xx with delays `[1, 2, 4]`s; `max_days_old=3`.
