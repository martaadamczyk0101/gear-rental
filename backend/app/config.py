import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATABASE_PATH = BACKEND_DIR / "booksy.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

SEED_FILE = PROJECT_ROOT / "seed.json"

# MVP admin bootstrap: on first run, an admin account is created with these
# credentials if one doesn't already exist. Override via env vars for anything
# beyond local dev.
ADMIN_EMAIL = os.environ.get("BOOKSY_ADMIN_EMAIL", "admin@booksy.com")
ADMIN_PASSWORD = os.environ.get("BOOKSY_ADMIN_PASSWORD", "admin123")

FRONTEND_ORIGIN = os.environ.get("BOOKSY_FRONTEND_ORIGIN", "http://localhost:5173")
