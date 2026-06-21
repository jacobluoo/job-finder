"""Quick assertions for filter edge cases."""
import filters

def _job(**kwargs):
    defaults = {"id": "x:1", "source": "x", "title": "", "company": "", "location": "", "area": [],
                "salary_min": None, "salary_max": None, "salary_is_predicted": False, "url": "", "date_posted": ""}
    return {**defaults, **kwargs}


# "intern" must NOT match via company name
assert not filters._keyword_match(_job(title="Office Admin", company="Intern Corp", location="")), \
    "company name should not feed keyword haystack"

# "intern" in title should match
assert filters._keyword_match(_job(title="Software Intern", location="")), \
    "intern in title should match"

# "intern" must NOT match "internal"
assert not filters._keyword_match(_job(title="Internal Auditor", location="")), \
    '"intern" should not match "internal"'

# "intern" should NOT match "internship" with padding — but "internship" IS in KEYWORDS so this is fine
# Confirm "internship" as its own keyword works
assert filters._keyword_match(_job(title="Internship Program", location="")), \
    "internship should match via KEYWORDS"

# VP should be excluded
assert filters._exclude_match(_job(title="VP Engineering")), \
    '"VP" title should be excluded'

# MVP must NOT be excluded
assert not filters._exclude_match(_job(title="MVP Engineer Intern")), \
    '"MVP" title must not be excluded via "vp" rule'

# Legitimate intern title must not be excluded
assert not filters._exclude_match(_job(title="Mechanical Engineer Intern")), \
    "plain intern title should not be excluded"

print("All assertions passed.")
