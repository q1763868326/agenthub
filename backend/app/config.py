import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
PACKAGES_DIR = Path(os.getenv("AGENTHUB_PACKAGES_DIR", BASE_DIR / "packages"))
DATA_DIR = Path(os.getenv("AGENTHUB_DATA_DIR", BASE_DIR / "data"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
DEFAULT_MODEL = os.getenv("AGENTHUB_DEFAULT_MODEL", "gpt-4o-mini")
AUTO_EXPERIENCE_EVERY_N_MESSAGES = int(os.getenv("AGENTHUB_AUTO_EXPERIENCE_EVERY_N_MESSAGES", "6"))
AUTO_EXPERIENCE_MIN_USER_CHARS = int(os.getenv("AGENTHUB_AUTO_EXPERIENCE_MIN_USER_CHARS", "8"))
