from app.models import HardwareStatus, Rental


def auth_header(user):
    return {"X-User-Id": str(user.id)}


def create_active_rental(db_session, hardware, user):
    """Directly establish an active rental, bypassing the request/approval
    workflow - used by tests that only care about return() behavior, which
    the approval workflow doesn't change."""
    rental = Rental(hardware_id=hardware.id, user_id=user.id)
    db_session.add(rental)
    hardware.status = HardwareStatus.IN_USE
    db_session.commit()
    db_session.refresh(rental)
    return rental


def test_admin_rent_available_hardware_succeeds_immediately(client, admin_user, available_hardware):
    resp = client.post(f"/hardware/{available_hardware.id}/rent", headers=auth_header(admin_user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "rented"
    assert body["hardware"]["status"] == "in use"


def test_regular_user_rent_creates_a_pending_request(client, regular_user, available_hardware):
    resp = client.post(f"/hardware/{available_hardware.id}/rent", headers=auth_header(regular_user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == "requested"
    # Hardware stays available - it isn't rented until an admin approves it.
    assert body["hardware"]["status"] == "available"

    mine = client.get("/rental-requests/mine", headers=auth_header(regular_user))
    assert mine.status_code == 200
    assert len(mine.json()) == 1
    assert mine.json()[0]["status"] == "pending"


def test_regular_user_cannot_request_already_in_use_hardware(
    client, admin_user, regular_user, available_hardware
):
    client.post(f"/hardware/{available_hardware.id}/rent", headers=auth_header(admin_user))
    resp = client.post(f"/hardware/{available_hardware.id}/rent", headers=auth_header(regular_user))
    assert resp.status_code == 409


def test_rent_in_repair_hardware_conflicts(client, regular_user, in_repair_hardware):
    resp = client.post(f"/hardware/{in_repair_hardware.id}/rent", headers=auth_header(regular_user))
    assert resp.status_code == 409


def test_rent_unknown_hardware_404s(client, regular_user):
    resp = client.post("/hardware/999/rent", headers=auth_header(regular_user))
    assert resp.status_code == 404


def test_duplicate_pending_request_from_same_user_conflicts(client, regular_user, available_hardware):
    client.post(f"/hardware/{available_hardware.id}/rent", headers=auth_header(regular_user))
    resp = client.post(f"/hardware/{available_hardware.id}/rent", headers=auth_header(regular_user))
    assert resp.status_code == 409


def test_two_different_users_can_both_have_pending_requests_for_the_same_item(
    client, regular_user, other_user, available_hardware
):
    first = client.post(f"/hardware/{available_hardware.id}/rent", headers=auth_header(regular_user))
    second = client.post(f"/hardware/{available_hardware.id}/rent", headers=auth_header(other_user))
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["outcome"] == "requested"
    assert second.json()["outcome"] == "requested"


def test_return_hardware_makes_it_available_again(client, db_session, regular_user, available_hardware):
    create_active_rental(db_session, available_hardware, regular_user)
    resp = client.post(f"/hardware/{available_hardware.id}/return", headers=auth_header(regular_user))
    assert resp.status_code == 200
    assert resp.json()["status"] == "available"


def test_returning_hardware_that_is_not_rented_conflicts(client, regular_user, available_hardware):
    resp = client.post(f"/hardware/{available_hardware.id}/return", headers=auth_header(regular_user))
    assert resp.status_code == 409


def test_non_owner_cannot_return_someone_elses_rental(
    client, db_session, regular_user, other_user, available_hardware
):
    create_active_rental(db_session, available_hardware, regular_user)
    resp = client.post(f"/hardware/{available_hardware.id}/return", headers=auth_header(other_user))
    assert resp.status_code == 403


def test_admin_can_return_someone_elses_rental(
    client, db_session, admin_user, regular_user, available_hardware
):
    create_active_rental(db_session, available_hardware, regular_user)
    resp = client.post(f"/hardware/{available_hardware.id}/return", headers=auth_header(admin_user))
    assert resp.status_code == 200


def test_my_rentals_lists_only_current_users_open_rentals(
    client, db_session, regular_user, other_user, available_hardware
):
    create_active_rental(db_session, available_hardware, regular_user)

    mine = client.get("/rentals/mine", headers=auth_header(regular_user))
    assert mine.status_code == 200
    data = mine.json()
    assert len(data) == 1
    assert data[0]["hardware"]["id"] == available_hardware.id

    others = client.get("/rentals/mine", headers=auth_header(other_user))
    assert others.json() == []


def test_returned_rental_no_longer_appears_in_my_rentals(
    client, db_session, regular_user, available_hardware
):
    create_active_rental(db_session, available_hardware, regular_user)
    client.post(f"/hardware/{available_hardware.id}/return", headers=auth_header(regular_user))
    resp = client.get("/rentals/mine", headers=auth_header(regular_user))
    assert resp.json() == []


def test_filter_hardware_by_status(client, regular_user, available_hardware, in_repair_hardware):
    resp = client.get("/hardware", params={"status": "in repair"}, headers=auth_header(regular_user))
    assert resp.status_code == 200
    ids = [h["id"] for h in resp.json()]
    assert in_repair_hardware.id in ids
    assert available_hardware.id not in ids


def test_search_hardware_by_name(client, regular_user, available_hardware, in_repair_hardware):
    resp = client.get("/hardware", params={"search": "laptop"}, headers=auth_header(regular_user))
    names = [h["name"] for h in resp.json()]
    assert "Test Laptop" in names
    assert "Broken Mouse" not in names


def test_sort_hardware_by_name_desc(client, regular_user, available_hardware, in_repair_hardware):
    resp = client.get(
        "/hardware", params={"sort_by": "name", "sort_dir": "desc"}, headers=auth_header(regular_user)
    )
    names = [h["name"] for h in resp.json()]
    assert names == sorted(names, reverse=True)
