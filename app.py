import logging
import threading
import time
from datetime import datetime, timezone

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

import config
import db
import run as pipeline
from email_sender import posted_day, posted_key, safe_url

app = Flask(__name__)
app.jinja_env.globals["next_status"] = db.next_status
db.init_db(config.DB_PATH)

CHECK_INTERVAL_SECONDS = 3600
APPLIED_VIA = ["Company website", "LinkedIn", "Indeed", "Email", "Referral", "Other"]

_run_lock = threading.Lock()


def _run_in_background(force: bool) -> bool:
    """Start a pipeline run on a thread. Returns False if one is already going."""
    if not _run_lock.acquire(blocking=False):
        return False

    def target():
        try:
            pipeline.main(force=force)
        finally:
            _run_lock.release()

    threading.Thread(target=target, daemon=True).start()
    return True


def _hourly_checker() -> None:
    # run.main() itself skips if the last good run was < MIN_HOURS_BETWEEN_RUNS ago.
    while True:
        _run_in_background(force=False)
        time.sleep(CHECK_INTERVAL_SECONDS)


@app.template_filter("ago")
def _ago(iso: str | None) -> str:
    if not iso:
        return "never"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    secs = (datetime.now(timezone.utc) - dt).total_seconds()
    if secs < 3600:
        return f"{max(int(secs // 60), 0)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


@app.template_filter("dayname")
def _dayname(day: str) -> str:
    """'2026-10-15' -> 'Thu, Oct 15' for the day pager."""
    if day == "none":
        return "No date"
    try:
        return datetime.fromisoformat(day).strftime("%a, %b %d")
    except ValueError:
        return day


@app.template_filter("date")
def _date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except ValueError:
        return iso


@app.route("/")
def index():
    view = request.args.get("view", "new")
    if view not in db.VIEWS:
        view = "new"
    q = request.args.get("q", "").strip()
    jobs = sorted(db.list_jobs(config.DB_PATH, view, q), key=posted_key, reverse=True)

    # One page per posting day, newest first; undated jobs get a last page ("none").
    by_day: dict[str, list[dict]] = {}
    for job in jobs:
        by_day.setdefault(posted_day(job) or "none", []).append(job)
    days = list(by_day)  # already newest-first because jobs are sorted
    day = request.args.get("day", "")
    if day not in by_day:
        day = days[0] if days else ""
    i = days.index(day) if day else 0

    return render_template(
        "index.html",
        jobs=by_day.get(day, []), view=view, q=q,
        day=day, days=[(d, len(by_day[d])) for d in days],
        newer_day=days[i - 1] if i > 0 else None,
        older_day=days[i + 1] if i + 1 < len(days) else None,
        counts=db.view_counts(config.DB_PATH),
        last_run=db.last_run(config.DB_PATH),
    )


@app.route("/go/<job_id>")
def go(job_id):
    job = db.get_job(config.DB_PATH, job_id) or abort(404)
    db.mark_viewed(config.DB_PATH, job_id)
    url = safe_url(job["url"] or "")
    if url == "#":
        return redirect(url_for("job_detail", job_id=job_id))
    return redirect(url)


@app.route("/jobs/<job_id>")
def job_detail(job_id):
    job = db.get_job(config.DB_PATH, job_id) or abort(404)
    return render_template(
        "job.html",
        job=job,
        events=db.job_events(config.DB_PATH, job_id),
        statuses=[s for s in db.STATUSES if s != "new"],
        applied_via=APPLIED_VIA,
    )


@app.route("/jobs/<job_id>/status", methods=["POST"])
def update_status(job_id):
    db.get_job(config.DB_PATH, job_id) or abort(404)
    status = request.form.get("status", "")
    if status not in db.STATUSES:
        abort(400)
    application_url = request.form.get("application_url", "").strip()
    if application_url and safe_url(application_url) == "#":
        application_url = ""  # only http(s) links
    db.set_status(
        config.DB_PATH, job_id, status,
        note=request.form.get("note", "").strip(),
        applied_via=request.form.get("applied_via", "").strip(),
        application_url=application_url,
    )
    next_url = request.form.get("next", "")
    if not next_url.startswith("/") or next_url.startswith("//"):  # local paths only
        next_url = url_for("job_detail", job_id=job_id)
    return redirect(next_url)


@app.route("/jobs/<job_id>/cycle", methods=["POST"])
def cycle_status(job_id):
    """One click on the status badge: move to the next status in STATUS_CYCLE."""
    job = db.get_job(config.DB_PATH, job_id) or abort(404)
    status = db.next_status(job["status"])
    db.set_status(config.DB_PATH, job_id, status)
    return jsonify(status=status, next=db.next_status(status))


@app.route("/run", methods=["POST"])
def start_run():
    started = _run_in_background(force=True)
    return jsonify(started=started), 202 if started else 409


@app.route("/run/status")
def run_status():
    running = _run_lock.locked()
    last = db.last_run(config.DB_PATH)
    log = "\n".join(pipeline.current_log) if running else (last or {}).get("log")
    return jsonify(running=running, run=last, log=log)


if __name__ == "__main__":
    # Keep per-request lines out of run.log and out of the live run log.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    threading.Thread(target=_hourly_checker, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
