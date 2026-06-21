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
    {"what": "mechanical engineer intern", "where": "Ontario"},
    {"what": "mechanical engineer co-op", "where": "Ontario"},
    {"what": "mechanical engineering student", "where": "Ontario"},
    {"what": "mechanical design intern", "where": "Ontario"},
    {"what": "mechanical engineer intern", "where": "remote"},
    {"what": "mechanical engineer co-op", "where": "remote"},

    # Automation & Controls
    {"what": "automation engineer co-op", "where": "Ontario"},
    {"what": "automation engineer intern", "where": "Ontario"},
    {"what": "controls engineer intern", "where": "Ontario"},
    {"what": "PLC programmer intern", "where": "Ontario"},

    # Robotics
    {"what": "robotics intern", "where": "Ontario"},
    {"what": "robotics engineer co-op", "where": "Ontario"},
    {"what": "robotics software intern", "where": "Ontario"},
    {"what": "robotics intern", "where": "remote"},

    # Embedded & Hardware
    {"what": "embedded systems intern", "where": "Ontario"},
    {"what": "embedded software intern", "where": "Ontario"},
    {"what": "firmware engineer intern", "where": "Ontario"},
    {"what": "hardware engineer intern", "where": "Ontario"},

    # AI / ML / Software adjacent
    {"what": "machine learning intern", "where": "Ontario"},
    {"what": "AI engineer intern", "where": "Ontario"},
    {"what": "software engineer intern", "where": "Ontario"},
    {"what": "data engineer intern", "where": "Ontario"},
    {"what": "computer vision intern", "where": "Ontario"},
    {"what": "machine learning intern", "where": "remote"},
    {"what": "AI engineer intern", "where": "remote"},

    # Aerospace
    {"what": "aerospace engineer intern", "where": "Ontario"},
    {"what": "aerospace engineer co-op", "where": "Ontario"},
    {"what": "structural engineer intern", "where": "Ontario"},

    # Manufacturing & Materials
    {"what": "manufacturing engineer intern", "where": "Ontario"},
    {"what": "manufacturing engineer co-op", "where": "Ontario"},
    {"what": "materials engineer intern", "where": "Ontario"},
    {"what": "process engineer intern", "where": "Ontario"},
    {"what": "quality engineer intern", "where": "Ontario"},

    # Product & Design
    {"what": "product design intern", "where": "Ontario"},
    {"what": "CAD designer intern", "where": "Ontario"},
    {"what": "design engineer intern", "where": "Ontario"},
    {"what": "R&D engineer intern", "where": "Ontario"},

    # General catch-alls
    {"what": "engineering intern", "where": "London Ontario"},
    {"what": "engineering co-op", "where": "London Ontario"},
    {"what": "engineering intern", "where": "Toronto"},
    {"what": "engineering co-op", "where": "Toronto"},
    {"what": "engineering intern", "where": "Waterloo Ontario"},
]

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

    # AI / software
    "machine learning", "computer vision", "python", "embedded linux",
    "ros", "fpga", "microcontroller", "arduino", "raspberry pi",

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
