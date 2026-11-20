import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_user():
    suffix = uuid.uuid4().hex
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test Operator",
            "email": f"operator-{suffix}@example.test",
            "password": "CorrectHorseBattery9!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_account_vehicle_and_work_order_flow():
    token = create_user()
    headers = auth(token)

    vehicle = client.post(
        "/api/vehicles",
        headers=headers,
        json={
            "vehicle_name": "Test Truck",
            "registration": f"KA{uuid.uuid4().hex[:8].upper()}",
            "vehicle_type": "Commercial truck",
            "make_model": "Test Model",
            "odometer": 12500,
        },
    )
    assert vehicle.status_code == 200
    vehicle_id = vehicle.json()["id"]

    order = client.post(
        "/api/work-orders",
        headers=headers,
        json={
            "vehicle_id": vehicle_id,
            "title": "Inspect brake system",
            "priority": "High",
            "description": "Test work order",
        },
    )
    assert order.status_code == 200
    assert order.json()["vehicle_id"] == vehicle_id

    summary = client.get("/api/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["vehicles"] == 1
    assert summary.json()["open_work_orders"] == 1


def test_tyre_screening_is_saved_to_account_history():
    token = create_user()
    headers = auth(token)

    result = client.post(
        "/api/tyres/screen",
        headers=headers,
        json={
            "tyre_position": "Front Left",
            "pressure_psi": 25,
            "temperature_c": 45,
            "speed_kmh": 40,
            "manufacturer_min_psi": 30,
            "manufacturer_max_psi": 36,
        },
    )
    assert result.status_code == 200
    assert result.json()["status"] == "Inspection required"

    history = client.get("/api/tyres/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["pressure_psi"] == 25
    assert "Pressure below supplied manufacturer minimum" in history.json()[0]["flags"]


def test_tyre_screening_rejects_invalid_oem_range():
    token = create_user()
    response = client.post(
        "/api/tyres/screen",
        headers=auth(token),
        json={
            "tyre_position": "Front Left",
            "pressure_psi": 32,
            "temperature_c": 45,
            "manufacturer_min_psi": 40,
            "manufacturer_max_psi": 35,
        },
    )
    assert response.status_code == 400


def test_vehicle_records_are_account_scoped():
    first_token = create_user()
    second_token = create_user()
    vehicle = client.post(
        "/api/vehicles",
        headers=auth(first_token),
        json={
            "vehicle_name": "Private vehicle",
            "registration": f"KA{uuid.uuid4().hex[:8].upper()}",
            "vehicle_type": "Passenger car",
            "make_model": "Private",
            "odometer": 100,
        },
    )
    assert vehicle.status_code == 200
    response = client.get("/api/vehicles", headers=auth(second_token))
    assert response.status_code == 200
    assert all(item["id"] != vehicle.json()["id"] for item in response.json())
