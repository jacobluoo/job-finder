import time
import logging
import math
from datetime import date, datetime

from jobspy import scrape_jobs

import config
from sources import BaseSource

logger = logging.getLogger(__name__)


class JobSpySource(BaseSource):
    name = "jobspy"

    def fetch(self) -> list[dict]:
        seen_ids: set[str] = set()
        results: list[dict] = []
        for i, query in enumerate(config.SEARCH_QUERIES):
            if i > 0:
                time.sleep(config.JOBSPY_DELAY_SECONDS)
            for job in self._fetch_query(query["what"], query["where"]):
                if job["id"] not in seen_ids:
                    seen_ids.add(job["id"])
                    results.append(job)
        return results

    def _fetch_query(self, what: str, where: str) -> list[dict]:
        remote = where.lower() == "remote"
        try:
            df = scrape_jobs(
                site_name=config.JOBSPY_SITES,
                search_term=what,
                location="Canada" if remote else "Toronto, ON",
                is_remote=remote,
                country_indeed="Canada",
                results_wanted=config.JOBSPY_RESULTS_WANTED,
                hours_old=config.JOBSPY_HOURS_OLD,
            )
        except Exception as exc:
            logger.warning("JobSpy query failed: what=%s where=%s: %s", what, where, exc)
            return []
        return [self._normalize(row) for row in df.to_dict("records")]

    def _normalize(self, raw: dict) -> dict:
        posted = _clean(raw.get("date_posted"))
        return {
            "id": f"jobspy:{raw['id']}",
            "source": _clean(raw.get("site")) or self.name,
            "title": _clean(raw.get("title")) or "",
            "company": _clean(raw.get("company")) or "Unknown",
            "location": _clean(raw.get("location")) or "Unknown",
            "area": [],
            "salary_min": _clean(raw.get("min_amount")),
            "salary_max": _clean(raw.get("max_amount")),
            "salary_is_predicted": False,
            "url": _clean(raw.get("job_url")) or "",
            "date_posted": posted.isoformat() if isinstance(posted, (date, datetime)) else (posted or ""),
        }


def _clean(value):
    """Map pandas NaN/NaT/None to None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if type(value).__name__ == "NaTType":
        return None
    return value
