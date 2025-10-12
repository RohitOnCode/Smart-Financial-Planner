
import os, warnings
from dotenv import load_dotenv
load_dotenv()

try:
    from bs4 import GuessedAtParserWarning
    warnings.filterwarnings("ignore", category=GuessedAtParserWarning)
except Exception:
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_STATIC_DIR = os.path.join(BASE_DIR, "ui", "static")
ARTIFACTS_DIR = os.path.join(UI_STATIC_DIR, "artifacts")
OUTPUTS_DIR = os.path.join(os.path.dirname(BASE_DIR), "outputs")
os.makedirs(ARTIFACTS_DIR, exist_ok=True); os.makedirs(OUTPUTS_DIR, exist_ok=True)

STRICT_VERIFICATION = os.getenv("STRICT_VERIFICATION","true").lower()=="true"
REQUIRE_TOPIC_TERMS = os.getenv("REQUIRE_TOPIC_TERMS","true").lower()=="true"
MIN_EVIDENCE_OVERLAP = int(os.getenv("MIN_EVIDENCE_OVERLAP","1"))

LOG_PATH = os.path.join(OUTPUTS_DIR,"run.log")
