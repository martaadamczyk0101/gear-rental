import datetime


def auth_header(user):
    return {"X-User-Id": str(user.id)}


def test_update_hardware_partially_updates_only_provided_fields(
    client, admin_user, available_hardware
):
    resp = client.patch(
        f"/hardware/{available_hardware.id}",
        json={"notes": "updated note"},
        headers=auth_header(admin_user),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["notes"] == "updated note"
    # Untouched fields stay as they were.
    assert body["name"] == available_hardware.name
    assert body["brand"] == available_hardware.brand


def test_update_hardware_can_change_name_brand_and_purchase_date(
    client, admin_user, available_hardware
):
    resp = client.patch(
        f"/hardware/{available_hardware.id}",
        json={"name": "Renamed Laptop", "brand": "NewBrand", "purchase_date": "2022-01-01"},
        headers=auth_header(admin_user),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Renamed Laptop"
    assert body["brand"] == "NewBrand"
    assert body["purchase_date"] == "2022-01-01"


def test_update_hardware_rejects_future_purchase_date(client, admin_user, available_hardware):
    future = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    resp = client.patch(
        f"/hardware/{available_hardware.id}",
        json={"purchase_date": future},
        headers=auth_header(admin_user),
    )
    assert resp.status_code == 422


def test_create_hardware_rejects_future_purchase_date(client, admin_user):
    future = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    resp = client.post(
        "/hardware",
        json={"name": "New Device", "brand": "Brand", "purchase_date": future},
        headers=auth_header(admin_user),
    )
    assert resp.status_code == 422


def test_create_hardware_accepts_todays_date(client, admin_user):
    today = datetime.date.today().isoformat()
    resp = client.post(
        "/hardware",
        json={"name": "New Device", "brand": "Brand", "purchase_date": today},
        headers=auth_header(admin_user),
    )
    assert resp.status_code == 201
    assert resp.json()["purchase_date"] == today


def test_non_admin_cannot_update_hardware(client, regular_user, available_hardware):
    resp = client.patch(
        f"/hardware/{available_hardware.id}",
        json={"notes": "hacked"},
        headers=auth_header(regular_user),
    )
    assert resp.status_code == 403


def test_update_unknown_hardware_404s(client, admin_user):
    resp = client.patch("/hardware/999", json={"notes": "x"}, headers=auth_header(admin_user))
    assert resp.status_code == 404
