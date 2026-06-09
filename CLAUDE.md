# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the pipeline

```bash
python run.py
```

Outputs to `logs/run.log` (file) and stdout. Exit code 0 = success, 1 = pipeline error.

To run via the Task Scheduler batch wrapper (identical behavior, also logs to `logs/scheduler.log`):
```bat
scheduler\run_daily.bat
```

## Environment setup

Copy credentials into `.env` at the project root. Required keys:
```
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=
RECIPIENT_EMAIL=
```

`GMAIL_APP_PASSWORD` must be a Gmail App Password (16-char), not the account password. `RECIPIENT_EMAIL` defaults to `jacob.rj.luo@gmail.com` if unset.

Install dependencies:
```bash
pip install -r requirements.txt
```

## Architecture

```
run.py                  # Pipeline orchestrator — entry point
config.py               # All constants; loaded from .env at import time
db.py                   # SQLite helpers: init_db, filter_new, mark_seen
filters.py              # apply_filters → _keyword_match + _location_match
email_sender.py         # build_html + send_digest (Gmail SMTP_SSL port 465)
sources/
  __init__.py           # BaseSource ABC — all sources must implement fetch()
  adzuna.py             # AdzunaSource — current only source
data/jobs.db            # SQLite dedup store (auto-created on first run)
logs/run.log            # Rotating log
```

**Pipeline flow** (`run.py`):
1. `db.init_db` — create table if not exists
2. Each source's `.fetch()` — returns normalized job dicts
3. `filters.apply_filters` — keyword + location filter
4. `db.filter_new` — bulk `SELECT IN` to drop already-seen IDs
5. `db.mark_seen` — `INSERT OR IGNORE` (done **before** `send_digest` intentionally — prevents duplicate emails if SMTP fails and the run is retried)
6. `email_sender.send_digest` — HTML + plain-text MIME email

## Normalized job dict contract

Every source must return dicts with these keys (defined by `BaseSource`):

| Key | Type | Notes |
|-----|------|-------|
| `id` | str | Source-prefixed, e.g. `"adzuna:12345"` |
| `source` | str | Source name |
| `title` | str | |
| `company` | str | |
| `location` | str | Display string (city-level for Adzuna) |
| `area` | list[str] | Geographic hierarchy array — used by location filter |
| `salary_min` | float\|None | |
| `salary_max` | float\|None | |
| `salary_is_predicted` | bool | |
| `url` | str | |
| `date_posted` | str | ISO 8601 |

The `area` field is critical: Adzuna's `location.display_name` is city-level only (e.g. `"Kitchener, Waterloo region"`), so `_location_match` in `filters.py` checks both `location` and the joined `area` array for Ontario/Canada/remote terms.

## Adding a new source

1. Create `sources/<name>.py` implementing `BaseSource` — `name` class attribute + `fetch() -> list[dict]`
2. Use source-prefixed IDs: `f"{self.name}:{raw_id}"`
3. Populate the `area` field (list of geographic strings) if the API provides it; otherwise set `[]`
4. Add any new credentials to `.env` and `config.py`
5. Register in `run.py`: add to the `sources` list in `main()`

## Key implementation details

- `config.py` uses `Path(__file__).parent` for `DB_PATH` and `LOG_PATH` — required for Task Scheduler (cwd is not the project directory when run by the scheduler)
- `db.filter_new` and `db.mark_seen` both guard `if not jobs: return` to avoid invalid `WHERE id IN ()` SQL
- Adzuna source retries on HTTP 429/5xx with delays `[1, 2, 4]` seconds; `max_days_old` controls how far back to pull (currently `3`)
- HTML emails use inline CSS only — Gmail strips `<style>` blocks
- `email_sender._escape()` HTML-escapes all job fields injected into the template
