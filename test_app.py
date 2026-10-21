"""End-to-end checks for the pipeline run guard and the website, against a temp DB.
Sources and email are stubbed, so nothing is fetched or sent."""
import os
import tempfile
import time

import config

_tmp = tempfile.mkdtemp()
config.DB_PATH = os.path.join(_tmp, "jobs.db")
config.LOG_PATH = os.path.join(_tmp, "run.log")

import db
import email_sender
import run
import app as site

JOBS = [
    {"id": "jobspy:li-1", "source": "linkedin", "title": "Mechanical Engineering Co-op",
     "company": "Acme", "location": "Toronto, ON, Canada", "area": [],
     "url": "https://example.com/1", "date_posted": "2026-10-14"},
    {"id": "jobspy:in-2", "source": "indeed", "title": "Robotics Intern",
     "company": "Bolt", "location": "Ottawa, Ontario, Canada", "area": [],
     "url": "javascript:alert(1)", "date_posted": "2026-10-15"},
    {"id": "jobspy:in-3", "source": "indeed", "title": "Finance Intern",  # filtered out
     "company": "Bank", "location": "Toronto, ON, Canada", "area": [],
     "url": "https://example.com/3", "date_posted": "2026-10-15"},
]


class _Stub:
    name = "stub"

    def fetch(self):
        return [dict(j) for j in JOBS]


class _Empty:
    name = "empty"

    def fetch(self):
        return []


sent: list[list[dict]] = []
run.AdzunaSource = _Empty
run.JobSpySource = _Stub
email_sender.send_digest = lambda jobs: sent.append(jobs)
client = site.app.test_client()

# First run stores the two in-scope jobs and emails them
assert run.main() == 0
assert db.last_run(config.DB_PATH)["status"] == "ok"
assert {j["id"] for j in db.list_jobs(config.DB_PATH, "all")} == {"jobspy:li-1", "jobspy:in-2"}
assert len(sent) == 1 and len(sent[0]) == 2

# A second run within MIN_HOURS_BETWEEN_RUNS is skipped (no new run row)
first_id = db.last_run(config.DB_PATH)["id"]
assert run.main() == 0
assert db.last_run(config.DB_PATH)["id"] == first_id, "non-forced run should be skipped"

# --force runs anyway; nothing new, so no email
assert run.main(force=True) == 0
assert db.last_run(config.DB_PATH)["id"] == first_id + 1
assert len(sent) == 1

# The New tab has one page per posting day, newest day first
html = client.get("/").get_data(as_text=True)
assert "Robotics Intern" in html and "Mechanical Engineering Co-op" not in html
assert "Older day" in html and "?view=new&amp;day=2026-10-14" in html
html = client.get("/?view=new&day=2026-10-14").get_data(as_text=True)
assert "Mechanical Engineering Co-op" in html and "Robotics Intern" not in html
assert "Robotics Intern" in client.get("/?day=bogus").get_data(as_text=True), "bad day falls back to newest"

# Search filters every tab and offers a Clear link back to the full list
html = client.get("/?view=new&q=robotics").get_data(as_text=True)
assert "Robotics Intern" in html and 'href="/?view=new">Clear</a>' in html
html = client.get("/?view=new&q=").get_data(as_text=True)
assert ">Clear</a>" not in html and "Older day" in html, "empty search shows everything"

# Email links open the job's day page, scrolled to the job
link = email_sender.site_link(JOBS[0])
assert link.endswith("/?view=new&day=2026-10-14#job-jobspy%3Ali-1"), link

# The email's direct link goes straight to the posting (not tracked)
assert 'href="https://example.com/1"' in email_sender.build_html(JOBS)

# Clicking a posting marks it viewed and redirects to it
resp = client.get("/go/jobspy%3Ali-1")
assert resp.status_code == 302 and resp.headers["Location"] == "https://example.com/1"
assert db.get_job(config.DB_PATH, "jobspy:li-1")["status"] == "viewed"

# A non-http posting URL is never redirected to
resp = client.get("/go/jobspy:in-2")
assert resp.status_code == 302 and "javascript" not in resp.headers["Location"]

# Marking applied saves where, and later updates build a timeline
client.post("/jobs/jobspy:li-1/status", data={
    "status": "applied", "applied_via": "LinkedIn",
    "application_url": "javascript:alert(1)", "note": "sent resume"})
job = db.get_job(config.DB_PATH, "jobspy:li-1")
assert job["status"] == "applied" and job["applied_via"] == "LinkedIn" and job["applied_at"]
assert job["application_url"] is None, "non-http application links are dropped"
client.post("/jobs/jobspy:li-1/status", data={"status": "interview", "note": "phone screen"})
events = [e["status"] for e in db.job_events(config.DB_PATH, "jobspy:li-1")]
assert events == ["interview", "applied", "viewed"]
assert "phone screen" in client.get("/jobs/jobspy:li-1").get_data(as_text=True)
assert db.view_counts(config.DB_PATH)["applied"] == 1

# Clicking again doesn't downgrade an applied job back to viewed
client.get("/go/jobspy:li-1")
assert db.get_job(config.DB_PATH, "jobspy:li-1")["status"] == "interview"

# Clicking the status badge steps through the wheel and wraps around,
# and a one-click "applied" keeps where-you-applied saved earlier
wheel = []
for _ in range(6):
    wheel.append(client.post("/jobs/jobspy:li-1/cycle").get_json()["status"])
assert wheel == ["offer", "rejected", "new", "viewed", "applied", "interview"], wheel
assert db.get_job(config.DB_PATH, "jobspy:li-1")["applied_via"] == "LinkedIn"
assert client.post("/jobs/nope/cycle").status_code == 404

# Unknown status and off-site "next" redirects are rejected
assert client.post("/jobs/jobspy:li-1/status", data={"status": "bogus"}).status_code == 400
resp = client.post("/jobs/jobspy:in-2/status", data={"status": "hidden", "next": "//evil.com"})
assert "evil.com" not in resp.headers["Location"]

# Refresh button: background run, and its log is returned every time
# (regression: the old app returned an empty log from the 2nd run on)
for _ in range(2):
    assert client.post("/run").status_code == 202
    while client.get("/run/status").get_json()["running"]:
        time.sleep(0.05)
    status = client.get("/run/status").get_json()
    assert status["run"]["status"] == "ok"
    assert "listings after filtering" in status["log"]

print("All app assertions passed.")
