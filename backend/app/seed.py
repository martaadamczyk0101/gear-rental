import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from .auth import hash_password
from .config import ADMIN_EMAIL, ADMIN_PASSWORD, SEED_FILE
from .database import Base, SessionLocal, engine
from .models import Hardware, HardwareStatus, User

logger = logging.getLogger("booksy.seed")

STATUS_ALIASES = {
    "available": HardwareStatus.AVAILABLE,
    "in use": HardwareStatus.IN_USE,
    "in repair": HardwareStatus.IN_REPAIR,
    "repair": HardwareStatus.IN_REPAIR,
}


def _normalize_status(raw_status) -> Optional[HardwareStatus]:
    if not isinstance(raw_status, str):
        return None
    return STATUS_ALIASES.get(raw_status.strip().lower())


def _normalize_purchase_date(raw_date):
    """Returns (date_or_None, was_valid). A missing date is valid (None);
    a present-but-unparseable date is invalid but non-fatal - the row is
    still seeded with a null purchase date."""
    if raw_date is None:
        return None, True
    if not isinstance(raw_date, str):
        return None, False
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").date(), True
    except ValueError:
        return None, False


def load_seed_rows(seed_path: Path = SEED_FILE) -> list:
    with open(seed_path) as f:
        return json.load(f)


def _combine_notes(row: dict) -> Optional[str]:
    """`notes` and `history` are both free-text, human-written context about a
    device (condition, incidents, etc.) - there's no separate "history" feature,
    so seed rows using either key are unified into the single `notes` column
    rather than silently dropping whichever key the schema doesn't recognize."""
    notes = (row.get("notes") or "").strip()
    history = (row.get("history") or "").strip()
    combined = " ".join(part for part in (notes, history) if part)
    return combined or None


def seed_hardware(db: Session, rows: list) -> None:
    if db.query(Hardware).count() > 0:
        logger.info("Hardware table already populated, skipping seed")
        return

    seen_source_ids = set()
    inserted = 0

    for row in rows:
        source_id = row.get("id")
        name = (row.get("name") or "").strip()
        brand = (row.get("brand") or "").strip()

        if source_id in seen_source_ids:
            logger.warning("Skipping row with duplicate seed id %s: %r", source_id, row)
            continue
        if not name:
            logger.warning("Skipping row with empty name: %r", row)
            continue
        if not brand:
            logger.warning("Skipping row with empty brand: %r", row)
            continue

        status = _normalize_status(row.get("status"))
        if status is None:
            logger.warning(
                "Skipping row %s (%s) with unrecognized status %r", source_id, name, row.get("status")
            )
            continue

        purchase_date, date_was_valid = _normalize_purchase_date(row.get("purchaseDate"))
        if not date_was_valid:
            logger.warning(
                "Row %s (%s) has an unparseable purchaseDate %r, storing as null",
                source_id,
                name,
                row.get("purchaseDate"),
            )

        seen_source_ids.add(source_id)
        db.add(
            Hardware(
                name=name,
                brand=brand,
                purchase_date=purchase_date,
                status=status,
                notes=_combine_notes(row),
            )
        )
        inserted += 1

    db.commit()
    logger.info("Seeded %d hardware rows out of %d in seed.json", inserted, len(rows))


def ensure_admin(db: Session) -> None:
    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing is not None:
        return

    db.add(User(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD), is_admin=True))
    db.commit()
    logger.info("Bootstrapped admin account %s", ADMIN_EMAIL)


def run_seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_admin(db)
        seed_hardware(db, load_seed_rows())
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_seed()
