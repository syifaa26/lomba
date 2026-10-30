"""Integration & unit tests for API-02: Auth, Family, and Device Pairing."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.database import Base, get_db
from app.main import app

# Shared in-memory SQLite database across threads for test client
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False
)


@pytest.fixture(autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """Create all schema tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide FastAPI test client with isolated database session override."""

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_root_and_health_endpoints(client: TestClient) -> None:
    """Verify root status and health check endpoints."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


def test_user_register_and_login(client: TestClient) -> None:
    """Verify user registration, JWT token generation, and login verification."""
    # 1. Register new user
    reg_payload = {
        "name": "Budi Santoso",
        "email": "budi@example.com",
        "password": "StrongPassword123!",
        "phone_number": "081234567890",
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    data_reg = res_reg.json()
    assert "access_token" in data_reg
    assert data_reg["user"]["email"] == "budi@example.com"
    token = data_reg["access_token"]

    # 2. Prevent duplicate email registration
    res_dup = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_dup.status_code == 400

    # 3. Login with correct credentials
    login_payload = {"email": "budi@example.com", "password": "StrongPassword123!"}
    res_login = client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    assert res_login.json()["access_token"] is not None

    # 4. Login with incorrect password
    res_bad_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "budi@example.com", "password": "WrongPassword"},
    )
    assert res_bad_pw.status_code == 401

    # 5. Access profile /me
    headers = {"Authorization": f"Bearer {token}"}
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["name"] == "Budi Santoso"

    # 6. Update FCM token
    res_fcm = client.put(
        "/api/v1/auth/fcm-token",
        json={"fcm_token": "fcm_token_abc_xyz"},
        headers=headers,
    )
    assert res_fcm.status_code == 200
    assert res_fcm.json()["fcm_token"] == "fcm_token_abc_xyz"


def test_auth_me_unauthorized(client: TestClient) -> None:
    """Verify unauthorized requests without token or with invalid token are rejected."""
    assert client.get("/api/v1/auth/me").status_code == 401
    bad_headers = {"Authorization": "Bearer invalid_token_xyz"}
    assert client.get("/api/v1/auth/me", headers=bad_headers).status_code == 401


def test_family_lifecycle_and_device_pairing(client: TestClient) -> None:
    """Verify family creation, join via invite code, vehicle pairing, and overview."""
    # Register User A (Father / Creator)
    res_a = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Ayah Budi",
            "email": "ayah@example.com",
            "password": "Password123!",
        },
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B (Child / Member)
    res_b = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Anak Sari",
            "email": "sari@example.com",
            "password": "Password123!",
        },
    )
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a Family
    res_fam = client.post(
        "/api/v1/families",
        json={"name": "Keluarga Bahagia"},
        headers=headers_a,
    )
    assert res_fam.status_code == 201
    family = res_fam.json()
    fam_id = family["id"]
    invite_code = family["invite_code"]
    assert len(invite_code) == 8

    # User B joins the family with invite code
    res_join = client.post(
        "/api/v1/families/join",
        json={"invite_code": invite_code, "role": "MEMBER"},
        headers=headers_b,
    )
    assert res_join.status_code == 200

    # User B checks my families
    res_my_fam = client.get("/api/v1/families/my", headers=headers_b)
    assert res_my_fam.status_code == 200
    assert len(res_my_fam.json()) == 1

    # User A pairs an Edge Raspberry Pi Device to the family
    res_dev = client.post(
        f"/api/v1/families/{fam_id}/devices",
        json={
            "device_uid": "pi4_innova_01",
            "vehicle_name": "Toyota Innova - B 1234 XYZ",
            "api_key": "custom_edge_api_key_123",
        },
        headers=headers_a,
    )
    assert res_dev.status_code == 201
    device_data = res_dev.json()
    assert device_data["device_uid"] == "pi4_innova_01"
    assert device_data["vehicle_name"] == "Toyota Innova - B 1234 XYZ"

    # Both users fetch Family Overview
    res_overview = client.get(
        f"/api/v1/families/{fam_id}/overview", headers=headers_b
    )
    assert res_overview.status_code == 200
    overview = res_overview.json()
    assert overview["family"]["name"] == "Keluarga Bahagia"
    assert len(overview["members"]) == 2
    assert len(overview["devices"]) == 1
    assert overview["devices"][0]["device_uid"] == "pi4_innova_01"


def test_family_and_device_error_cases(client: TestClient) -> None:
    """Verify error responses for invalid invite code and unauthorized device pairing."""
    res_user = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Orang Asing",
            "email": "asing@example.com",
            "password": "Password123!",
        },
    )
    token = res_user.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt join with non-existent invite code
    res_join = client.post(
        "/api/v1/families/join",
        json={"invite_code": "NONEXIST"},
        headers=headers,
    )
    assert res_join.status_code == 404

    # Attempt device pairing to a family the user doesn't belong to
    res_pair = client.post(
        "/api/v1/families/999/devices",
        json={"device_uid": "pi4_fake"},
        headers=headers,
    )
    assert res_pair.status_code == 403

    # Attempt get overview for non-joined family
    res_ov = client.get("/api/v1/families/999/overview", headers=headers)
    assert res_ov.status_code == 403

