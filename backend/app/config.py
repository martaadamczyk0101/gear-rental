import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

DATABASE_PATH = BACKEND_DIR / "booksy.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

SEED_FILE = PROJECT_ROOT / "seed.json"

# MVP admin bootstrap: on first run, an admin account is created with these
# credentials if one doesn't already exist. Override via env vars for anything
# beyond local dev.
ADMIN_EMAIL = os.environ.get("BOOKSY_ADMIN_EMAIL", "admin@booksy.com")
ADMIN_PASSWORD = os.environ.get("BOOKSY_ADMIN_PASSWORD", "admin123")

FRONTEND_ORIGIN = os.environ.get("BOOKSY_FRONTEND_ORIGIN", "http://localhost:5173")

# Semantic search (Part 2): requires a real key, no default. Without one, the
# /hardware/semantic-search endpoint responds 503 rather than failing to start.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_SEARCH_MODEL = os.environ.get("ANTHROPIC_SEARCH_MODEL", "claude-sonnet-5")
