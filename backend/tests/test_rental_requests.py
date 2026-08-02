from app.models import HardwareStatus


def auth_header(user):
    return {"X-User-Id": str(user.id)}


def request_rental(client, user, hardware):
    resp = client.post(f"/hardware/{hardware.id}/rent", headers=auth_header(user))
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "requested"


def test_non_admin_cannot_list_requests(client, regular_user, available_hardware):
    request_rental(client, regular_user, available_hardware)
    resp = client.get("/rental-requests", headers=auth_header(regular_user))
    assert resp.status_code == 403


def test_admin_can_list_pending_requests(client, admin_user, regular_user, available_hardware):
    request_rental(client, regular_user, available_hardware)
    resp = client.get("/rental-requests", headers=auth_header(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"
    assert data[0]["hardware"]["id"] == available_hardware.id
    assert data[0]["user"]["id"] == regular_user.id


def test_pending_count_reflects_open_requests(client, admin_user, regular_user, available_hardware):
    assert client.get("/rental-requests/pending-count", headers=auth_header(admin_user)).json() == {
        "pending": 0
    }
    request_rental(client, regular_user, available_hardware)
    assert client.get("/rental-requests/pending-count", headers=auth_header(admin_user)).json() == {
        "pending": 1
    }


def test_approve_request_rents_the_item_and_marks_request_approved(
    client, db_session, admin_user, regular_user, available_hardware
):
    request_rental(client, regular_user, available_hardware)
    request_id = client.get("/rental-requests", headers=auth_header(admin_user)).json()[0]["id"]

    resp = client.post(f"/rental-requests/{request_id}/approve", headers=auth_header(admin_user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"

    db_session.refresh(available_hardware)
    assert available_hardware.status == HardwareStatus.IN_USE

    mine = client.get("/rentals/mine", headers=auth_header(regular_user)).json()
    assert len(mine) == 1
    assert mine[0]["hardware"]["id"] == available_hardware.id


def test_approving_one_request_auto_rejects_other_pending_requests_for_same_item(
    client, admin_user, regular_user, other_user, available_hardware
):
    request_rental(client, regular_user, available_hardware)
    request_rental(client, other_user, available_hardware)

    pending = client.get("/rental-requests", headers=auth_header(admin_user)).json()
    assert len(pending) == 2
    first_request_id = next(r["id"] for r in pending if r["user"]["id"] == regular_user.id)
    second_request_id = next(r["id"] for r in pending if r["user"]["id"] == other_user.id)

    approve_resp = client.post(f"/rental-requests/{first_request_id}/approve", headers=auth_header(admin_user))
    assert approve_resp.status_code == 200

    # The sibling request must no longer be acceptable.
    reject_check = client.get("/rental-requests?status=rejected", headers=auth_header(admin_user)).json()
    assert any(r["id"] == second_request_id for r in reject_check)

    still_pending = client.get("/rental-requests", headers=auth_header(admin_user)).json()
    assert still_pending == []

    second_approve_attempt = client.post(
        f"/rental-requests/{second_request_id}/approve", headers=auth_header(admin_user)
    )
    assert second_approve_attempt.status_code == 409


def test_approve_fails_if_item_became_unavailable_in_the_meantime(
    client, db_session, admin_user, regular_user, available_hardware
):
    request_rental(client, regular_user, available_hardware)
    request_id = client.get("/rental-requests", headers=auth_header(admin_user)).json()[0]["id"]

    # Simulate the item becoming unavailable through some other path (e.g. an
    # admin renting it directly) before this request gets approved.
    available_hardware.status = HardwareStatus.IN_REPAIR
    db_session.commit()

    resp = client.post(f"/rental-requests/{request_id}/approve", headers=auth_header(admin_user))
    assert resp.status_code == 409


def test_reject_request_marks_it_rejected_and_leaves_hardware_available(
    client, db_session, admin_user, regular_user, available_hardware
):
    request_rental(client, regular_user, available_hardware)
    request_id = client.get("/rental-requests", headers=auth_header(admin_user)).json()[0]["id"]

    resp = client.post(f"/rental-requests/{request_id}/reject", headers=auth_header(admin_user))
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    db_session.refresh(available_hardware)
    assert available_hardware.status == HardwareStatus.AVAILABLE


def test_deciding_an_already_decided_request_conflicts(client, admin_user, regular_user, available_hardware):
    request_rental(client, regular_user, available_hardware)
    request_id = client.get("/rental-requests", headers=auth_header(admin_user)).json()[0]["id"]

    client.post(f"/rental-requests/{request_id}/reject", headers=auth_header(admin_user))
    resp = client.post(f"/rental-requests/{request_id}/reject", headers=auth_header(admin_user))
    assert resp.status_code == 409


def test_unknown_request_id_404s(client, admin_user):
    resp = client.post("/rental-requests/999/approve", headers=auth_header(admin_user))
    assert resp.status_code == 404


def test_mine_only_shows_the_current_users_own_pending_requests(
    client, regular_user, other_user, available_hardware, in_repair_hardware
):
    request_rental(client, regular_user, available_hardware)

    mine = client.get("/rental-requests/mine", headers=auth_header(regular_user)).json()
    assert len(mine) == 1

    others_view = client.get("/rental-requests/mine", headers=auth_header(other_user)).json()
    assert others_view == []
