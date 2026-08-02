from app.models import Hardware
from app.seed import seed_hardware


def test_history_field_is_folded_into_notes(db_session):
    rows = [
        {
            "id": 1,
            "name": "MacBook Air M2",
            "brand": "Apple",
            "purchaseDate": "2023-08-01",
            "status": "Available",
            "history": "Returned by user with liquid damage.",
        }
    ]
    seed_hardware(db_session, rows)
    item = db_session.query(Hardware).one()
    assert item.notes == "Returned by user with liquid damage."


def test_notes_and_history_are_combined_when_both_present(db_session):
    rows = [
        {
            "id": 1,
            "name": "Test Laptop",
            "brand": "TestBrand",
            "purchaseDate": "2023-08-01",
            "status": "Available",
            "notes": "Battery swelling.",
            "history": "Returned with liquid damage.",
        }
    ]
    seed_hardware(db_session, rows)
    item = db_session.query(Hardware).one()
    assert item.notes == "Battery swelling. Returned with liquid damage."


def test_row_with_neither_notes_nor_history_gets_null_notes(db_session):
    rows = [
        {
            "id": 1,
            "name": "Test Laptop",
            "brand": "TestBrand",
            "purchaseDate": "2023-08-01",
            "status": "Available",
        }
    ]
    seed_hardware(db_session, rows)
    item = db_session.query(Hardware).one()
    assert item.notes is None
