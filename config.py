import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

ADZUNA_APP_ID: str = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY: str = os.getenv("ADZUNA_APP_KEY", "")
GMAIL_ADDRESS: str = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL: str = os.getenv("RECIPIENT_EMAIL", "jacob.rj.luo@gmail.com")

DB_PATH: str = str(BASE_DIR / "data" / "jobs.db")
LOG_PATH: str = str(BASE_DIR / "logs" / "run.log")

SEARCH_QUERIES: list[dict] = [
    # Mechanical
    {"what": "mechanical engineer intern", "where": "Toronto"},
    {"what": "mechanical engineer co-op", "where": "Toronto"},
    {"what": "mechanical engineering student", "where": "Toronto"},
    {"what": "mechanical design intern", "where": "Toronto"},
    {"what": "mechanical engineer intern", "where": "remote"},
    {"what": "mechanical engineer co-op", "where": "remote"},

    # Automation & Controls
    {"what": "automation engineer co-op", "where": "Toronto"},
    {"what": "automation engineer intern", "where": "Toronto"},
    {"what": "controls engineer intern", "where": "Toronto"},
    {"what": "PLC programmer intern", "where": "Toronto"},

    # Robotics
    {"what": "robotics intern", "where": "Toronto"},
    {"what": "robotics engineer co-op", "where": "Toronto"},
    {"what": "robotics software intern", "where": "Toronto"},
    {"what": "robotics intern", "where": "remote"},

    # Embedded & Hardware
    {"what": "embedded systems intern", "where": "Toronto"},
    {"what": "embedded software intern", "where": "Toronto"},
    {"what": "firmware engineer intern", "where": "Toronto"},
    {"what": "hardware engineer intern", "where": "Toronto"},

    # Aerospace
    {"what": "aerospace engineer intern", "where": "Toronto"},
    {"what": "aerospace engineer co-op", "where": "Toronto"},
    {"what": "structural engineer intern", "where": "Toronto"},

    # Manufacturing & Materials
    {"what": "manufacturing engineer intern", "where": "Toronto"},
    {"what": "manufacturing engineer co-op", "where": "Toronto"},
    {"what": "materials engineer intern", "where": "Toronto"},
    {"what": "process engineer intern", "where": "Toronto"},
    {"what": "quality engineer intern", "where": "Toronto"},

    # Product & Design
    {"what": "product design intern", "where": "Toronto"},
    {"what": "CAD designer intern", "where": "Toronto"},
    {"what": "design engineer intern", "where": "Toronto"},
    {"what": "R&D engineer intern", "where": "Toronto"},

    # General catch-alls
    {"what": "engineering intern", "where": "Toronto"},
    {"what": "engineering co-op", "where": "Toronto"},
]

JOBSPY_SITES: list[str] = ["indeed", "linkedin"]
JOBSPY_RESULTS_WANTED: int = 25
JOBSPY_HOURS_OLD: int = 72      # matches Adzuna max_days_old=3
JOBSPY_DELAY_SECONDS: float = 3

# All keyword lists are matched against the job TITLE only, as whole words /
# phrases, case-insensitive ("intern" does not match "internal", "milton" does
# not match "hamilton"). A job passes when:
#   1. it has a STUDENT_KEYWORDS term, AND
#   2. it has a CORE_KEYWORDS term, OR a DISCIPLINE_KEYWORDS term with no
#      OFF_SCOPE_KEYWORDS term, AND
#   3. it has no EXCLUDE_KEYWORDS term.

# Role-level signal: the title must say it's a student / entry-level role.
STUDENT_KEYWORDS: list[str] = [
    "intern", "interns", "internship", "internships",
    "co-op", "coop", "co op", "pey", "student", "students",
    "work term", "placement", "undergrad", "undergraduate",
    "new grad", "new grads", "new graduate", "new graduates",
    "entry level", "entry-level", "junior", "jr",
    "trainee", "engineer in training", "eit",
    # French (Quebec postings)
    "stage", "stagiaire", "stagiaires",
]

# Unambiguously hardware/mechanical: passes even alongside an off-scope word
# (e.g. "Embedded Software Intern", "Robotics Software Co-op").
CORE_KEYWORDS: list[str] = [
    "mechanical", "mechatronics", "mechatronic", "robotics", "robotic", "robot",
    "embedded", "firmware", "hardware", "electrical", "electronics",
    "aerospace", "avionics", "manufacturing",
    "mécanique", "électromécanique", "aérospatiale",
    # Tools & platforms
    "cad", "solidworks", "catia", "creo", "ansys", "autocad", "inventor",
    "simulink", "labview", "plc", "scada", "fpga", "pcb", "microcontroller",
]

# In scope, but these words also show up in software/business/civil titles,
# so they only count when no OFF_SCOPE_KEYWORDS term is present.
DISCIPLINE_KEYWORDS: list[str] = [
    "engineer", "engineering", "engineers", "technologist", "technician",
    "automation", "controls", "structural", "materials", "industrial",
    "process engineer", "process engineering", "quality", "reliability",
    "validation", "r&d", "research & development", "research and development",
    "lean", "continuous improvement", "operational excellence", "matlab",
    "test", "testing", "testlab", "test lab",
    "génie", "ingénierie", "ingénieur", "ingénieure", "ingénieur.e",
]

# Kills a DISCIPLINE_KEYWORDS match (but not a CORE_KEYWORDS match).
OFF_SCOPE_KEYWORDS: list[str] = [
    # Software / IT / data
    "software", "developer", "programmer", "full stack", "frontend", "backend",
    "web", "cloud", "devops", "data", "ai", "machine learning", "ml",
    "analytics", "it", "security", "cybersecurity", "network", "compiler",
    # Civil / environmental
    "civil", "geotechnical", "geoscience", "environmental", "water",
    "wastewater", "transportation", "highways",
    # Business
    "finance", "financial", "accounting", "audit", "marketing", "sales",
    "business", "supply chain",
    # French
    "logiciel", "informatique", "civil", "environnement",
]

# Any match drops the job, regardless of the lists above.
EXCLUDE_KEYWORDS: list[str] = [
    # Seniority
    "senior", "sr", "lead", "principal", "staff engineer", "manager",
    "director", "vp", "vice president", "head of", "chief", "executive",

    # Graduate level
    "phd", "ph.d", "doctorate", "doctoral", "postdoc", "post-doc",
    "graduate intern", "graduate engineer", "graduate developer",

    # Professional designations you don't have yet
    "p.eng", "pmp", "licensed engineer",

    # Look like hardware/automation roles but aren't
    "robotic process automation", "rpa", "test automation", "qa automation",
    "ehs", "health & safety", "health and safety",
]
