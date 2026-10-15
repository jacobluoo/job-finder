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

KEYWORDS: list[str] = [
    # Original
    "mechanical", "automation", "robotics", "manufacturing", "embedded",
    "cad", "solidworks", "mechatronics", "intern", "co-op", "coop",
    "co op", "entry level", "junior", "student",

    # Engineering disciplines
    "aerospace", "controls", "firmware", "hardware", "structural",
    "materials", "process", "quality", "design", "R&D", "product",

    # Tools & software
    "matlab", "simulink", "ansys", "catia", "inventor", "autocad",
    "creo", "nx", "labview", "plc", "scada",

    # Hardware platforms
    "fpga", "microcontroller", "arduino", "raspberry pi",

    # Job type signals
    "4 month", "8 month", "12 month", "work term", "placement",
    "new grad", "undergrad", "internship",
]

EXCLUDE_KEYWORDS: list[str] = [
    # Experience requirements
    "5+ years", "7+ years", "10+ years", "senior", "lead", "principal",
    "staff engineer", "manager", "director", " vp ", "vice president",
    "head of", "chief", "executive",

    # Graduate level
    "phd", "ph.d", "doctorate", "doctoral", "postdoc", "post-doc",
    "masters required", "msc required", "graduate degree required",
    "graduate intern", "graduate engineer", "graduate developer",

    # Professional designations you don't have yet
    "p.eng", "professional engineer required", "pmp", "licensed engineer",

    # Clearly not entry level
    "proven track record", "extensive experience", "seasoned",
    "expert level", "deep expertise",

        # Permanent roles not open to students
    "permanent only", "no students", "full time permanent",
    "must be eligible to work permanently",

    # Way out of scope
    "nurse", "doctor", "lawyer", "accountant", "teacher",
    "sales representative", "real estate",
]
