import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
PACKAGES_DIR = Path(os.getenv("AGENTHUB_PACKAGES_DIR", BASE_DIR / "packages"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
DEFAULT_MODEL = os.getenv("AGENTHUB_DEFAULT_MODEL", "gpt-4o-mini")
