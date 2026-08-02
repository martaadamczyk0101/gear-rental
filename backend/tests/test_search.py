import datetime

from app import llm
from app.llm import SemanticSearchUnavailable
from app.models import Hardware, HardwareStatus


def auth_header(user):
    return {"X-User-Id": str(user.id)}


def test_missing_query_is_rejected(client, regular_user):
    resp = client.get("/hardware/semantic-search", headers=auth_header(regular_user))
    assert resp.status_code == 422


def test_unauthenticated_request_is_rejected(client):
    resp = client.get("/hardware/semantic-search", params={"q": "a phone"})
    assert resp.status_code == 401


def test_missing_api_key_returns_503(client, regular_user, available_hardware, monkeypatch):
    monkeypatch.setattr(llm, "ANTHROPIC_API_KEY", None)
    resp = client.get(
        "/hardware/semantic-search",
        params={"q": "a laptop"},
        headers=auth_header(regular_user),
    )
    assert resp.status_code == 503


def test_anthropic_error_returns_503(client, regular_user, available_hardware, monkeypatch):
    def boom(query, inventory):
        raise SemanticSearchUnavailable("Semantic search request failed")

    monkeypatch.setattr("app.routers.search.find_matching_ids", boom)
    resp = client.get(
        "/hardware/semantic-search",
        params={"q": "a laptop"},
        headers=auth_header(regular_user),
    )
    assert resp.status_code == 503


def test_successful_match_returns_hardware_in_returned_order(
    client, regular_user, available_hardware, in_repair_hardware, monkeypatch
):
    def fake_find_matching_ids(query, inventory):
        assert query == "a laptop"
        assert {item["id"] for item in inventory} == {available_hardware.id, in_repair_hardware.id}
        # Deliberately return in_repair first to verify ordering is preserved,
        # and confirm status isn't used to filter results out.
        return [in_repair_hardware.id, available_hardware.id]

    monkeypatch.setattr("app.routers.search.find_matching_ids", fake_find_matching_ids)

    resp = client.get(
        "/hardware/semantic-search",
        params={"q": "a laptop"},
        headers=auth_header(regular_user),
    )
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert ids == [in_repair_hardware.id, available_hardware.id]


def test_inventory_sent_to_the_model_includes_purchase_date(
    client, regular_user, db_session, monkeypatch
):
    # Regression test: the LLM must actually receive purchase_date, brand, and
    # notes for every item - not just id/name/status - or it can't answer
    # questions like "what was purchased before 2023".
    old_item = Hardware(
        name="Old Laptop",
        brand="Dell",
        purchase_date=datetime.date(2021, 5, 1),
        notes="hand-me-down",
        status=HardwareStatus.AVAILABLE,
    )
    db_session.add(old_item)
    db_session.commit()
    db_session.refresh(old_item)

    captured = {}

    def fake_find_matching_ids(query, inventory):
        captured["inventory"] = inventory
        return []

    monkeypatch.setattr("app.routers.search.find_matching_ids", fake_find_matching_ids)

    resp = client.get(
        "/hardware/semantic-search",
        params={"q": "devices purchased before 2023"},
        headers=auth_header(regular_user),
    )
    assert resp.status_code == 200

    sent = next(item for item in captured["inventory"] if item["id"] == old_item.id)
    assert sent["purchase_date"] == "2021-05-01"
    assert sent["brand"] == "Dell"
    assert sent["notes"] == "hand-me-down"


def test_unknown_ids_from_the_model_are_silently_dropped(
    client, regular_user, available_hardware, monkeypatch
):
    def fake_find_matching_ids(query, inventory):
        return [available_hardware.id, 999999]

    monkeypatch.setattr("app.routers.search.find_matching_ids", fake_find_matching_ids)

    resp = client.get(
        "/hardware/semantic-search",
        params={"q": "a laptop"},
        headers=auth_header(regular_user),
    )
    assert resp.status_code == 200
    assert [item["id"] for item in resp.json()] == [available_hardware.id]
