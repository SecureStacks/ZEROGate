import pytest
from app.seed.seed_data import seed_database

@pytest.fixture(autouse=True)
def populate_seed(db_session):
    seed_database(db_session)

def test_list_users(admin_client):
    response = admin_client.get("/api/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 5
    usernames = [u["username"] for u in users]
    assert "alice" in usernames
    assert "bob" in usernames
    assert "carol" in usernames
    assert "admin" in usernames
    assert "vendor-01" in usernames

def test_get_user_by_id(admin_client):
    users = admin_client.get("/api/users").json()
    alice = next(u for u in users if u["username"] == "alice")
    
    response = admin_client.get(f"/api/users/{alice['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "alice"
    assert data["role"] == "Developer"

def test_list_devices(admin_client):
    response = admin_client.get("/api/devices")
    assert response.status_code == 200
    devices = response.json()
    assert len(devices) >= 5
    postures = {d["posture_status"] for d in devices}
    assert "Healthy" in postures
    assert "Unhealthy" in postures
    assert "Compromised" in postures

def test_list_resources(admin_client):
    response = admin_client.get("/api/resources")
    assert response.status_code == 200
    resources = response.json()
    resource_names = [r["name"] for r in resources]
    assert "Git Repository" in resource_names
    assert "HR Database" in resource_names
    assert "Finance Database" in resource_names
    assert "CI/CD Server" in resource_names
    assert "Cloud Infrastructure" in resource_names
    assert "Internal API" in resource_names

def test_get_demo_scenarios(admin_client):
    response = admin_client.get("/api/demo/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 3
    scenario_ids = [s["id"] for s in scenarios]
    assert "scenario-a" in scenario_ids
    assert "scenario-b" in scenario_ids
    assert "scenario-c" in scenario_ids
    
    scenario_a = next(s for s in scenarios if s["id"] == "scenario-a")
    assert scenario_a["username"] == "alice"
    assert scenario_a["network"]["ip_reputation"] == "Trusted"
    assert scenario_a["device_posture"] == "Healthy"

def test_create_access_request_endpoint(alice_client):
    users = alice_client.get("/api/users").json()
    devices = alice_client.get("/api/devices").json()
    resources = alice_client.get("/api/resources").json()

    alice = next(u for u in users if u["username"] == "alice")
    device = next(d for d in devices if d["owner_user_id"] == alice["id"])
    resource = next(r for r in resources if r["name"] == "Git Repository")

    payload = {
        "user_id": alice["id"],
        "device_id": device["id"],
        "resource_id": resource["id"],
        "source_ip": "10.0.4.55",
        "ip_reputation": "Trusted",
        "network_type": "Corporate",
        "is_vpn": False,
        "is_tor": False,
        "is_known_network": True,
        "country": "India",
        "city": "Bengaluru",
        "unusual_time": False,
        "unusual_location": False,
        "unusual_resource": False,
        "failed_attempts": 0,
        "recent_resource_count": 1,
        "source_segment": "Development",
    }

    response = alice_client.post("/api/access-requests", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["source_ip"] == "10.0.4.55"
    assert data["ip_reputation"] == "Trusted"

    # Test retrieval
    get_res = alice_client.get(f"/api/access-requests/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == data["id"]
