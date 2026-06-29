import config


def apply_filters(jobs: list[dict]) -> list[dict]:
    return [j for j in jobs if _keyword_match(j) and _location_match(j) and not _exclude_match(j)]


def _keyword_match(job: dict) -> bool:
    haystack = " " + " ".join([
        (job.get("title") or ""),
        (job.get("location") or ""),
    ]).lower() + " "
    return any(f" {kw} " in haystack for kw in config.KEYWORDS)


_GTA_TERMS = {
    # City of Toronto and inner boroughs
    "toronto", "north york", "scarborough", "etobicoke", "east york",
    # Peel Region
    "mississauga", "brampton", "caledon",
    # York Region
    "vaughan", "markham", "richmond hill", "newmarket", "aurora",
    # Durham Region
    "ajax", "pickering", "whitby", "oshawa",
    # Halton Region
    "oakville", "burlington", "milton",
    # Region labels Adzuna uses in area[]
    "city of toronto", "peel region", "york region", "durham region", "halton region",
    # Remote
    "remote",
}

def _location_match(job: dict) -> bool:
    location = (job.get("location") or "").lower()
    area = " ".join(job.get("area") or []).lower()
    searchable = f"{location} {area}"
    return any(term in searchable for term in _GTA_TERMS)

def _exclude_match(job: dict) -> bool:
    title = (job.get("title") or "").lower()
    searchable = f" {title} "
    return any(exclude in searchable for exclude in config.EXCLUDE_KEYWORDS)