from datetime import datetime, timezone
import uuid
from app.models.schemas import TrackingEvent, TrackingResponse
from app.providers.apsrtc import ProviderError

def payload(tracking_number="12345678"):
    return {"tracking_number": tracking_number, "mobile_number": "9123456789", "provider": "APSRTC", "origin": "Fictional Origin", "destination": "Fictional Destination", "current_status": "BOOKED", "events": [], "monitoring_enabled": False}

def test_saved_parcel_is_private_and_persists(authenticated_client):
    first = authenticated_client.post("/api/parcels", json=payload())
    second = authenticated_client.post("/api/parcels", json=payload())
    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert len(authenticated_client.get("/api/parcels").json()) == 1
    assert authenticated_client.delete(f"/api/parcels/{first.json()['id']}").status_code == 204

def test_check_updates_only_the_authenticated_users_matching_parcel(authenticated_client, monkeypatch):
    first = authenticated_client.post("/api/parcels", json=payload()).json()
    second = authenticated_client.post("/api/parcels", json=payload("87654321")).json()
    calls=[]
    class Provider:
        async def track(self, tracking_number, mobile_number):
            calls.append((tracking_number, mobile_number))
            return TrackingResponse(tracking_number=tracking_number, current_status="IN_TRANSIT", events=[TrackingEvent(status="IN_TRANSIT")], last_successful_check=datetime.now(timezone.utc))
    monkeypatch.setattr("app.main.APSRTCProvider", Provider)
    response = authenticated_client.post(f"/api/parcels/{first['id']}/check", json={})
    assert response.status_code == 200 and calls == [("12345678", "9123456789")]
    saved = authenticated_client.get("/api/parcels").json()
    assert next(item for item in saved if item["id"] == first["id"])["current_status"] == "IN_TRANSIT"
    assert next(item for item in saved if item["id"] == second["id"])["current_status"] == "BOOKED"

def test_failed_check_preserves_previous_result(authenticated_client, monkeypatch):
    parcel = authenticated_client.post("/api/parcels", json=payload()).json()
    class Provider:
        async def track(self, *_): raise ProviderError("Service unavailable")
    monkeypatch.setattr("app.main.APSRTCProvider", Provider)
    assert authenticated_client.post(f"/api/parcels/{parcel['id']}/check", json={}).status_code == 502
    assert authenticated_client.get("/api/parcels").json()[0]["current_status"] == "BOOKED"

def test_user_cannot_access_another_users_parcel(authenticated_client):
    parcel = authenticated_client.post("/api/parcels", json=payload()).json()
    from app.main import app
    from fastapi.testclient import TestClient
    from app.models.database import SessionLocal, User
    from app.auth import hash_password
    username = f"other{uuid.uuid4().hex[:12]}"
    other = TestClient(app); session=SessionLocal(); session.add(User(username=username, password_hash=hash_password("test-only-password"))); session.commit(); session.close()
    assert other.post("/api/auth/login", json={"username":username,"password":"test-only-password"}).status_code == 200
    assert other.get("/api/parcels").json() == []
    assert other.post(f"/api/parcels/{parcel['id']}/check", json={}).status_code == 404
    assert other.delete(f"/api/parcels/{parcel['id']}").status_code == 404
