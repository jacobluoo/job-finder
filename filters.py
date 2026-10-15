import re

import config


def apply_filters(jobs: list[dict]) -> list[dict]:
    return [j for j in jobs if _keyword_match(j) and _location_match(j) and not _exclude_match(j)]


def _pattern(terms) -> re.Pattern:
    """Whole-word/phrase matcher: no letter or digit allowed on either side."""
    alts = "|".join(re.escape(t.lower()) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<![a-z0-9])(?:{alts})(?![a-z0-9])")


def _has(pattern: re.Pattern, text: str) -> bool:
    return pattern.search(text) is not None


_STUDENT = _pattern(config.STUDENT_KEYWORDS)
_CORE = _pattern(config.CORE_KEYWORDS)
_DISCIPLINE = _pattern(config.DISCIPLINE_KEYWORDS)
_OFF_SCOPE = _pattern(config.OFF_SCOPE_KEYWORDS)
_EXCLUDE = _pattern(config.EXCLUDE_KEYWORDS)


def _title(job: dict) -> str:
    return (job.get("title") or "").lower()


def _keyword_match(job: dict) -> bool:
    title = _title(job)
    if not _has(_STUDENT, title):
        return False
    if _has(_CORE, title):
        return True
    return _has(_DISCIPLINE, title) and not _has(_OFF_SCOPE, title)


# "Toronto, ON, Canada" / "Waterdown, Ontario, Canada"; Adzuna puts the
# province in area[].
_ONTARIO = _pattern(["ontario", "on", "greater toronto area", "remote"])


def _location_match(job: dict) -> bool:
    location = (job.get("location") or "").lower()
    area = " ".join(job.get("area") or []).lower()
    return _has(_ONTARIO, f"{location} {area}")


def _exclude_match(job: dict) -> bool:
    return _has(_EXCLUDE, _title(job))
