import pytest
from fastapi.testclient import TestClient
from app.main import app

# We will create a client inside each test to trigger lifespan, or use a fixture.
@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client

def test_unauthenticated_access(test_client):
    response = test_client.get("/api/users/me")
    assert response.status_code == 401
    
    response = test_client.get("/api/policies")
    assert response.status_code == 401

def test_login_invalid_credentials(test_client):
    response = test_client.post("/api/auth/login", data={"username": "alice", "password": "wrongpassword"})
    assert response.status_code in (400, 401)

def test_alice_normal_user_access(test_client):
    # Login as alice
    login_res = test_client.post("/api/auth/login", data={"username": "alice", "password": "User@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Access permitted functionality
    me_res = test_client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "alice"
    
    # Attempt to access admin-only functionality
    admin_res = test_client.post("/api/policies", json={"name": "Test", "description": "test", "priority": 1, "action": "ALLOW", "rules": []}, headers=headers)
    assert admin_res.status_code == 403

def test_admin_access(test_client):
    # Login as admin
    login_res = test_client.post("/api/auth/login", data={"username": "admin", "password": "Admin@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Access admin functionality
    admin_res = test_client.get("/api/policies", headers=headers)
    assert admin_res.status_code == 200

def test_cross_user_access(test_client):
    # Login as alice
    alice_login = test_client.post("/api/auth/login", data={"username": "alice", "password": "User@123"})
    alice_token = alice_login.json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    
    # Get all users (needs admin, wait, users API might need admin or self?)
    # Wait, /api/users might be protected. Let's try /api/access-requests/{id}
    # We need another user's access request. We can create one as admin or bob, and try to read it as alice.
    
    bob_login = test_client.post("/api/auth/login", data={"username": "bob", "password": "User@123"})
    bob_token = bob_login.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    
    # Bob creates an access request
    me_res = test_client.get("/api/auth/me", headers=bob_headers)
    bob_id = me_res.json()["id"]
    
    # Just to find a device and resource
    devices = test_client.get("/api/devices", headers=bob_headers).json()
    bob_device = next(d for d in devices if d["owner_user_id"] == bob_id)
    resources = test_client.get("/api/resources", headers=bob_headers).json()
    resource = resources[0]
    
    ar_payload = {
        "user_id": bob_id,
        "device_id": bob_device["id"],
        "resource_id": resource["id"],
        "source_ip": "10.10.10.10",
        "ip_reputation": "Trusted",
        "network_type": "Corporate",
        "is_vpn": False,
        "is_tor": False,
        "is_known_network": True,
        "country": "US",
        "city": "NY",
        "unusual_time": False,
        "unusual_location": False,
        "unusual_resource": False,
        "failed_attempts": 0,
        "recent_resource_count": 1,
        "source_segment": "HR",
    }
    
    ar_res = test_client.post("/api/access-requests", json=ar_payload, headers=bob_headers)
    assert ar_res.status_code == 201
    ar_id = ar_res.json()["id"]
    
    # Alice tries to read Bob's request
    alice_read = test_client.get(f"/api/access-requests/{ar_id}", headers=alice_headers)
    assert alice_read.status_code in (403, 404)
