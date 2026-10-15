import time
import logging
import requests
import config
from sources import BaseSource

logger = logging.getLogger(__name__)

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/ca/search"
MAX_PAGES = 5
RESULTS_PER_PAGE = 50


class AdzunaSource(BaseSource):
    name = "adzuna"

    def fetch(self) -> list[dict]:
        if not config.ADZUNA_APP_ID or not config.ADZUNA_APP_KEY:
            logger.error("Adzuna credentials missing — set ADZUNA_APP_ID/ADZUNA_APP_KEY in .env")
            return []
        seen_ids: set[str] = set()
        results: list[dict] = []
        for query in config.SEARCH_QUERIES:
            for job in self._fetch_query(query["what"], query["where"]):
                if job["id"] not in seen_ids:
                    seen_ids.add(job["id"])
                    results.append(job)
        return results

    def _fetch_query(self, what: str, where: str) -> list[dict]:
        jobs: list[dict] = []
        for page in range(1, MAX_PAGES + 1):
            data = self._get_page(what, where, page)
            if data is None:
                break
            page_results = data.get("results", [])
            if not page_results:
                break
            for raw in page_results:
                jobs.append(self._normalize(raw))
            total = data.get("count", 0)
            if page * RESULTS_PER_PAGE >= total:
                break
        return jobs

    def _get_page(self, what: str, where: str, page: int) -> dict | None:
        url = f"{ADZUNA_BASE}/{page}"
        params = {
            "app_id": config.ADZUNA_APP_ID,
            "app_key": config.ADZUNA_APP_KEY,
            "what": what,
            "where": where,
            "results_per_page": RESULTS_PER_PAGE,
            "max_days_old": 3,
        }
        headers = {"Accept": "application/json"}
        delays = [1, 2, 4]
        for attempt, delay in enumerate(delays):
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=15)
                if resp.status_code == 429 or resp.status_code >= 500:
                    logger.warning("Adzuna HTTP %s on attempt %d, retrying in %ds", resp.status_code, attempt + 1, delay)
                    time.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    logger.error("Adzuna HTTP %s (not retrying): %s", resp.status_code, resp.text[:200])
                    return None
                return resp.json()
            except requests.RequestException as exc:
                logger.warning("Request error on attempt %d: %s", attempt + 1, exc)
                if attempt < len(delays) - 1:
                    time.sleep(delay)
        logger.error("Adzuna query failed after retries: what=%s where=%s page=%d", what, where, page)
        return None

    def _normalize(self, raw: dict) -> dict:
        return {
            "id": f"adzuna:{raw['id']}",
            "source": self.name,
            "title": raw.get("title", ""),
            "company": raw.get("company", {}).get("display_name", "Unknown"),
            "location": raw.get("location", {}).get("display_name", "Unknown"),
            "area": raw.get("location", {}).get("area", []),
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "salary_is_predicted": bool(raw.get("salary_is_predicted", 0)),
            "url": raw.get("redirect_url", ""),
            "date_posted": raw.get("created", ""),
        }
