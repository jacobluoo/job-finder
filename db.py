import sqlite3
from datetime import datetime, timedelta, timezone

# Statuses a job can be in. "new" and "viewed" are set automatically;
# the rest are set by the user from the website.
STATUSES = ["new", "viewed", "applied", "interview", "offer",
            "rejected", "ghosted", "withdrawn", "hidden"]

# Clicking a job's status on the website steps through this list (and wraps).
# Statuses outside it (ghosted, withdrawn, hidden) are set from the Details page.
STATUS_CYCLE = ["new", "viewed", "applied", "interview", "offer", "rejected"]


def next_status(status: str) -> str:
    if status not in STATUS_CYCLE:
        return STATUS_CYCLE[0]
    return STATUS_CYCLE[(STATUS_CYCLE.index(status) + 1) % len(STATUS_CYCLE)]


# Website tabs -> statuses shown in that tab (None = everything).
VIEWS: dict[str, list[str] | None] = {
    "new": ["new"],
    "viewed": ["viewed"],
    "applied": ["applied", "interview", "offer"],
    "closed": ["rejected", "ghosted", "withdrawn"],
    "hidden": ["hidden"],
    "all": None,
}

_JOB_COLUMNS = {
    "status": "TEXT NOT NULL DEFAULT 'new'",
    "viewed_at": "TEXT",
    "applied_at": "TEXT",
    "applied_via": "TEXT",
    "application_url": "TEXT",
    "updated_at": "TEXT",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with _connect(db_path) as conn:
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
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)")}
        for name, decl in _JOB_COLUMNS.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE jobs ADD COLUMN {name} {decl}")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS status_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL REFERENCES jobs(id),
                status TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                fetched INTEGER,
                filtered INTEGER,
                new_count INTEGER,
                log TEXT
            )
        """)
        conn.commit()


# ---------------------------------------------------------------- pipeline

def filter_new(jobs: list[dict], db_path: str) -> list[dict]:
    if not jobs:
        return []
    with _connect(db_path) as conn:
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
    now = _now()
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
    with _connect(db_path) as conn:
        conn.executemany(
            """INSERT OR IGNORE INTO jobs
               (id, source, title, company, location,
                salary_min, salary_max, salary_is_predicted,
                url, date_posted, first_seen)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()


# ---------------------------------------------------------------- runs

def start_run(db_path: str) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'running')", (_now(),)
        )
        conn.commit()
        return cur.lastrowid


def finish_run(db_path: str, run_id: int, status: str, log: str,
               fetched: int | None = None, filtered: int | None = None,
               new_count: int | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """UPDATE runs SET finished_at=?, status=?, log=?,
                   fetched=?, filtered=?, new_count=?
               WHERE id=?""",
            (_now(), status, log, fetched, filtered, new_count, run_id),
        )
        conn.commit()


def last_run(db_path: str, status: str | None = None) -> dict | None:
    sql = "SELECT * FROM runs"
    params: tuple = ()
    if status:
        sql += " WHERE status=?"
        params = (status,)
    with _connect(db_path) as conn:
        row = conn.execute(sql + " ORDER BY id DESC LIMIT 1", params).fetchone()
    return dict(row) if row else None


def run_in_progress(db_path: str, max_age_hours: float = 2) -> bool:
    """True if a run started recently and hasn't finished. Older 'running'
    rows are treated as crashed so they can't block runs forever."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM runs WHERE status='running' AND started_at > ? LIMIT 1",
            (cutoff,),
        ).fetchone()
    return row is not None


def hours_since_last_success(db_path: str) -> float | None:
    run = last_run(db_path, status="ok")
    if not run or not run["finished_at"]:
        return None
    finished = datetime.fromisoformat(run["finished_at"])
    return (datetime.now(timezone.utc) - finished).total_seconds() / 3600


# ---------------------------------------------------------------- website

def list_jobs(db_path: str, view: str = "new", q: str = "") -> list[dict]:
    statuses = VIEWS.get(view, VIEWS["new"])
    sql = "SELECT * FROM jobs WHERE 1=1"
    params: list = []
    if statuses is not None:
        sql += f" AND status IN ({','.join('?' * len(statuses))})"
        params += statuses
    if q:
        sql += " AND (title LIKE ? OR company LIKE ? OR location LIKE ?)"
        params += [f"%{q}%"] * 3
    with _connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, params)]


def view_counts(db_path: str) -> dict[str, int]:
    with _connect(db_path) as conn:
        by_status = {r["status"]: r["n"] for r in
                     conn.execute("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status")}
    return {
        view: sum(by_status.values()) if statuses is None
        else sum(by_status.get(s, 0) for s in statuses)
        for view, statuses in VIEWS.items()
    }


def get_job(db_path: str, job_id: str) -> dict | None:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row) if row else None


def job_events(db_path: str, job_id: str) -> list[dict]:
    with _connect(db_path) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM status_events WHERE job_id=? ORDER BY id DESC", (job_id,)
        )]


def mark_viewed(db_path: str, job_id: str) -> None:
    """Move a job from 'new' to 'viewed'. Never downgrades later statuses."""
    now = _now()
    with _connect(db_path) as conn:
        cur = conn.execute(
            "UPDATE jobs SET status='viewed', viewed_at=?, updated_at=? "
            "WHERE id=? AND status='new'",
            (now, now, job_id),
        )
        if cur.rowcount:
            conn.execute(
                "INSERT INTO status_events (job_id, status, note, created_at) VALUES (?,?,?,?)",
                (job_id, "viewed", None, now),
            )
        conn.commit()


def set_status(db_path: str, job_id: str, status: str, note: str = "",
               applied_via: str | None = None,
               application_url: str | None = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"unknown status: {status}")
    now = _now()
    with _connect(db_path) as conn:
        conn.execute("UPDATE jobs SET status=?, updated_at=? WHERE id=?", (status, now, job_id))
        if status == "viewed":
            conn.execute("UPDATE jobs SET viewed_at=COALESCE(viewed_at, ?) WHERE id=?", (now, job_id))
        if status == "applied":
            # Blank fields (e.g. a one-click status change) keep what was saved before.
            conn.execute(
                "UPDATE jobs SET applied_at=COALESCE(applied_at, ?), "
                "applied_via=COALESCE(?, applied_via), "
                "application_url=COALESCE(?, application_url) WHERE id=?",
                (now, applied_via or None, application_url or None, job_id),
            )
        conn.execute(
            "INSERT INTO status_events (job_id, status, note, created_at) VALUES (?,?,?,?)",
            (job_id, status, note or None, now),
        )
        conn.commit()
