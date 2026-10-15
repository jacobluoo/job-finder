"""Quick assertions for filter edge cases."""
import filters

def _job(**kwargs):
    defaults = {"id": "x:1", "source": "x", "title": "", "company": "", "location": "", "area": [],
                "salary_min": None, "salary_max": None, "salary_is_predicted": False, "url": "", "date_posted": ""}
    return {**defaults, **kwargs}


# "intern" must NOT match via company name
assert not filters._keyword_match(_job(title="Office Admin", company="Intern Corp", location="")), \
    "company name should not feed keyword haystack"

# "intern" + an in-scope discipline in title should match
assert filters._keyword_match(_job(title="Mechanical Intern", location="")), \
    "intern in title should match"

# "intern" must NOT match "internal"
assert not filters._keyword_match(_job(title="Internal Mechanical Auditor", location="")), \
    '"intern" should not match "internal"'

# Confirm "internship" as its own keyword works
assert filters._keyword_match(_job(title="Engineering Internship Program", location="")), \
    "internship should match via STUDENT_KEYWORDS"

# Student signal alone is not enough — needs a hardware/mechanical discipline
assert not filters._keyword_match(_job(title="Finance Operations Intern")), \
    "non-engineering intern should not match"
assert not filters._keyword_match(_job(title="Mechanical Engineering Analyst")), \
    "discipline without a student/entry-level signal should not match"

# Off-scope words veto generic engineering titles...
assert not filters._keyword_match(_job(title="Software Engineering, Intern")), \
    "software engineering intern should not match"
assert not filters._keyword_match(_job(title="Civil Engineering Co-op Student")), \
    "civil engineering co-op should not match"
assert filters._keyword_match(_job(title="Validation Engineering Co-op")), \
    "generic engineering co-op without off-scope words should match"

# ...but not core hardware ones
assert filters._keyword_match(_job(title="Embedded Software Intern")), \
    "embedded software intern should match despite 'software'"

# VP should be excluded
assert filters._exclude_match(_job(title="VP Engineering")), \
    '"VP" title should be excluded'

# MVP must NOT be excluded
assert not filters._exclude_match(_job(title="MVP Engineer Intern")), \
    '"MVP" title must not be excluded via "vp" rule'

# "lead" must not match "leadership"
assert not filters._exclude_match(_job(title="Leadership Development Engineering Intern")), \
    '"lead" must not match "leadership"'

# Look-alike roles are excluded outright
assert filters._exclude_match(_job(title="Student Intern, Robotic Process Automation Developer (IT)")), \
    "RPA (software) should be excluded"

# Legitimate intern title must not be excluded
assert not filters._exclude_match(_job(title="Mechanical Engineer Intern")), \
    "plain intern title should not be excluded"

# Location: anywhere in Ontario, nowhere else
assert filters._location_match(_job(location="Waterdown, ON, Canada"))
assert filters._location_match(_job(location="Kanata, Ontario, Canada"))
assert filters._location_match(_job(location="Greater Toronto Area, Canada"))
assert filters._location_match(_job(location="Toronto", area=["Canada", "Ontario", "Toronto"]))
assert not filters._location_match(_job(location="Montreal, Quebec, Canada"))
assert not filters._location_match(_job(location="Greater Vancouver Metropolitan Area"))

print("All assertions passed.")
