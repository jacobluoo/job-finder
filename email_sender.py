import smtplib
import config
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote, urlsplit


def build_html(jobs: list[dict]) -> str:
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    rows = "".join(_row_html(job, i) for i, job in enumerate(jobs))
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:20px;font-family:Arial,sans-serif;background:#f0f2f5;">
  <div style="max-width:900px;margin:0 auto;background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
    <div style="background:#1a1a2e;padding:24px 32px;">
      <h1 style="margin:0;color:#ffffff;font-size:22px;">Job Digest</h1>
      <p style="margin:6px 0 0;color:#a0a8c0;font-size:14px;">{len(jobs)} new listing(s) &middot; {today}</p>
      <a href="{_escape(site_link())}" style="display:inline-block;margin-top:14px;padding:8px 16px;background:#2563eb;color:#ffffff;border-radius:6px;text-decoration:none;font-size:14px;font-weight:600;">Open Job Finder</a>
    </div>
    <div style="padding:24px 32px;">
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#1a1a2e;">
            <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Job Title</th>
            <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Company</th>
            <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Location</th>
            <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Posted</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </div>
    <div style="padding:16px 32px;background:#f8f9fa;border-top:1px solid #e0e0e0;">
      <p style="margin:0;color:#888;font-size:12px;">Links open your local Job Finder ({_escape(config.SITE_URL)}) &mdash; it must be running. &middot; {today}</p>
    </div>
  </div>
</body>
</html>"""


def _row_html(job: dict, index: int) -> str:
    bg = "#ffffff" if index % 2 == 0 else "#f8f9fa"
    title = _escape(job.get("title", ""))
    url = _escape(site_link(job))
    company = _escape(job.get("company", ""))
    location = _escape(job.get("location", ""))
    posted = _format_date(job.get("date_posted", ""))
    return f"""<tr style="background:{bg};">
      <td style="padding:10px 12px;border-bottom:1px solid #e8e8e8;">
        <a href="{url}" style="color:#2563eb;text-decoration:none;font-weight:500;">{title}</a>
      </td>
      <td style="padding:10px 12px;border-bottom:1px solid #e8e8e8;color:#374151;">{company}</td>
      <td style="padding:10px 12px;border-bottom:1px solid #e8e8e8;color:#374151;">{location}</td>
      <td style="padding:10px 12px;border-bottom:1px solid #e8e8e8;color:#6b7280;white-space:nowrap;">{posted}</td>
    </tr>"""


def site_link(job: dict | None = None) -> str:
    """Link into the local website's New tab — for a job, the page for its
    posting day, scrolled to it. Postings are opened from the site so clicks
    get tracked there."""
    url = f"{config.SITE_URL}/?view=new"
    if not job:
        return url
    return f"{url}&day={posted_day(job) or 'none'}#job-{quote(job['id'], safe='')}"


def _format_salary(job: dict) -> str:
    lo = job.get("salary_min")
    hi = job.get("salary_max")
    est = " (est.)" if job.get("salary_is_predicted") else ""
    if lo and hi:
        return f"${lo:,.0f}–${hi:,.0f}/yr{est}"
    if lo:
        return f"${lo:,.0f}/yr{est}"
    if hi:
        return f"${hi:,.0f}/yr{est}"
    return "Not listed"


def _format_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return iso


def safe_url(url: str) -> str:
    try:
        scheme = urlsplit(url).scheme.lower()
    except ValueError:
        return "#"
    return url if scheme in ("http", "https") else "#"


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def posted_key(job: dict) -> datetime:
    """Sort key: posting date, with undated listings treated as oldest."""
    try:
        dt = datetime.fromisoformat((job.get("date_posted") or "").replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def posted_day(job: dict) -> str:
    """Posting date as YYYY-MM-DD ('' if unknown) — the website shows one day per page."""
    dt = posted_key(job)
    return "" if dt.year == datetime.min.year else dt.date().isoformat()


def send_digest(jobs: list[dict]) -> None:
    jobs = sorted(jobs, key=posted_key, reverse=True)  # newest first
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    subject = f"[Job Digest] {len(jobs)} new listing(s) — {today}"

    plain_lines = [f"{j.get('title','')} @ {j.get('company','')}" for j in jobs]
    plain_body = f"Open Job Finder: {site_link()}\n\n" + "\n".join(plain_lines)
    html_body = build_html(jobs)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_ADDRESS
    msg["To"] = config.RECIPIENT_EMAIL
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
        server.sendmail(config.GMAIL_ADDRESS, config.RECIPIENT_EMAIL, msg.as_string())
