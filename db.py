import sqlite3
from datetime import datetime, timezone


def init_db(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
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
        """)
        conn.commit()


def filter_new(jobs: list[dict], db_path: str) -> list[dict]:
    if not jobs:
        return []
    with sqlite3.connect(db_path) as conn:
        ids = [j["id"] for j in jobs]
        placeholders = ",".join("?" * len(ids))
        seen = {
            row[0]
            for row in conn.execute(
                f"SELECT id FROM jobs WHERE id IN ({placeholders})", ids
            )
        }
    return [j for j in jobs if j["id"] not in seen]


def mark_seen(jobs: list[dict], db_path: str) -> None:
    if not jobs:
        return
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            j["id"],
            j.get("source", ""),
            j.get("title", ""),
            j.get("company", ""),
            j.get("location", ""),
            j.get("salary_min"),
            j.get("salary_max"),
            int(j.get("salary_is_predicted", False)),
            j.get("url", ""),
            j.get("date_posted", ""),
            now,
        )
        for j in jobs
    ]
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """INSERT OR IGNORE INTO jobs
               (id, source, title, company, location,
                salary_min, salary_max, salary_is_predicted,
                url, date_posted, first_seen)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()
