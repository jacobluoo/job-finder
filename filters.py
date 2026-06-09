import config


def apply_filters(jobs: list[dict]) -> list[dict]:
    return [j for j in jobs if _keyword_match(j) and _location_match(j) and not _exclude_match(j)]


def _keyword_match(job: dict) -> bool:
    haystack = " ".join([
        (job.get("title") or ""),
        (job.get("company") or ""),
        (job.get("location") or ""),
    ]).lower()
    return any(kw in haystack for kw in config.KEYWORDS)


def _location_match(job: dict) -> bool:
    location = (job.get("location") or "").lower()
    area = " ".join(job.get("area") or []).lower()
    title = (job.get("title") or "").lower()
    searchable = f"{location} {area} {title}"
    return any(term in searchable for term in ["ontario", " on,", ", on", "remote"])

def _exclude_match(job: dict) -> bool:
    title = (job.get("title") or "").lower()
    searchable = title
    return any(exclude in searchable for exclude in config.EXCLUDE_KEYWORDS)