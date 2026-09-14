import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.enums import UserRole, DevicePosture, IPReputation, NetworkType, PolicyEffect, UserStatus
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource
from app.models.access_request import AccessRequest
from app.models.policy import Policy
from app.policy.evaluator import PolicyEvaluator
from app.risk.models import RiskAssessment, RiskLevel
from app.policy.seed import seed_policies
from app.seed.seed_data import seed_database
import uuid
from fastapi.testclient import TestClient
from app.main import app

from sqlalchemy.pool import StaticPool
import pytest
@pytest.fixture(autouse=True)
def db(db_session):
    seed_database(db_session)
    seed_policies(db_session)
    return db_session

def create_mock_risk(score: int) -> RiskAssessment:
    level = RiskLevel.LOW
    if score >= 40:
        level = RiskLevel.MEDIUM
    if score >= 70:
        level = RiskLevel.HIGH
    return RiskAssessment(
        score=score,
        level=level,
        raw_score=score,
        factors=[],
        summary="Mock Risk"
    )

def test_developer_git_access_low_risk(db_session):
    user = db_session.query(User).filter_by(username="alice").first()
    device = db_session.query(Device).filter_by(device_name="Alice MacBook Pro (Corporate)").first()
    resource = db_session.query(Resource).filter_by(name="Git Repository").first()
    access_request = AccessRequest(
        id=str(uuid.uuid4()), user_id=user.id, device_id=device.id, resource_id=resource.id,
        network_type=NetworkType.CORPORATE, ip_reputation=IPReputation.TRUSTED,
        is_known_network=True, source_ip="10.0.4.15", source_segment="Development"
    )
    risk = create_mock_risk(15)
    policies = db_session.query(Policy).all()

    decision = PolicyEvaluator.evaluate_access(user, device, resource, access_request, risk, policies)
    assert decision.decision == PolicyEffect.ALLOW
    assert decision.policy_name == "Developer Git Access"

def test_developer_git_access_medium_risk_stepup(db_session):
    user = db_session.query(User).filter_by(username="alice").first()
    device = db_session.query(Device).filter_by(device_name="Alice MacBook Pro (Corporate)").first()
    resource = db_session.query(Resource).filter_by(name="Git Repository").first()
    access_request = AccessRequest(
        id=str(uuid.uuid4()), user_id=user.id, device_id=device.id, resource_id=resource.id,
        network_type=NetworkType.CORPORATE, ip_reputation=IPReputation.TRUSTED,
        is_known_network=True, source_ip="10.0.4.15", source_segment="Development"
    )
    risk = create_mock_risk(60) # MEDIUM risk
    policies = db_session.query(Policy).all()

    decision = PolicyEvaluator.evaluate_access(user, device, resource, access_request, risk, policies)
    assert decision.decision == PolicyEffect.MFA_REQUIRED
    assert decision.policy_name == "Developer Elevated Risk Step-Up"

def test_critical_risk_deny(db_session):
    user = db_session.query(User).filter_by(username="alice").first()
    device = db_session.query(Device).filter_by(device_name="Alice MacBook Pro (Corporate)").first()
    resource = db_session.query(Resource).filter_by(name="Git Repository").first()
    access_request = AccessRequest(
        id=str(uuid.uuid4()), user_id=user.id, device_id=device.id, resource_id=resource.id,
        network_type=NetworkType.CORPORATE, ip_reputation=IPReputation.TRUSTED,
        is_known_network=True, source_ip="10.0.4.15", source_segment="Development"
    )
    risk = create_mock_risk(75) # HIGH risk
    policies = db_session.query(Policy).all()

    decision = PolicyEvaluator.evaluate_access(user, device, resource, access_request, risk, policies)
    assert decision.decision == PolicyEffect.DENY
    assert decision.policy_name == "Critical Risk Block"

def test_compromised_device_deny(db_session):
    user = db_session.query(User).filter_by(username="alice").first()
    device = db_session.query(Device).filter_by(device_name="Alice Compromised Workstation").first()
    resource = db_session.query(Resource).filter_by(name="Git Repository").first()
    access_request = AccessRequest(
        id=str(uuid.uuid4()), user_id=user.id, device_id=device.id, resource_id=resource.id,
        network_type=NetworkType.CORPORATE, ip_reputation=IPReputation.TRUSTED,
        is_known_network=True, source_ip="10.0.4.15", source_segment="Development"
    )
    risk = create_mock_risk(20) # even if risk is low, compromised device should block
    policies = db_session.query(Policy).all()

    decision = PolicyEvaluator.evaluate_access(user, device, resource, access_request, risk, policies)
    assert decision.decision == PolicyEffect.DENY
    assert decision.policy_name == "Compromised Device Block"

def test_default_deny_no_policy_matches(db_session):
    user = db_session.query(User).filter_by(username="vendor-01").first() # Vendor
    device = db_session.query(Device).filter_by(device_name="Vendor Contractor Laptop").first()
    resource = db_session.query(Resource).filter_by(name="HR Database").first()
    access_request = AccessRequest(
        id=str(uuid.uuid4()), user_id=user.id, device_id=device.id, resource_id=resource.id,
        network_type=NetworkType.CORPORATE, ip_reputation=IPReputation.TRUSTED,
        is_known_network=True, source_ip="10.0.4.15", source_segment="Development"
    )
    risk = create_mock_risk(10)
    policies = db_session.query(Policy).all()

    decision = PolicyEvaluator.evaluate_access(user, device, resource, access_request, risk, policies)
    assert decision.decision == PolicyEffect.DENY
    assert "Default Deny" in decision.reason

def test_disabled_user_deny(db_session):
    user = User(id="temp-user", username="disabled_user", status=UserStatus.DISABLED)
    device = db_session.query(Device).filter_by(device_name="Alice MacBook Pro (Corporate)").first()
    resource = db_session.query(Resource).filter_by(name="Git Repository").first()
    access_request = AccessRequest(id="req", source_segment="Development")
    risk = create_mock_risk(10)
    policies = db_session.query(Policy).all()
    
    decision = PolicyEvaluator.evaluate_access(user, device, resource, access_request, risk, policies)
    assert decision.decision == PolicyEffect.DENY
    assert "disabled" in decision.reason.lower()

def test_disabled_resource_deny(db_session):
    user = db_session.query(User).filter_by(username="alice").first()
    device = db_session.query(Device).filter_by(device_name="Alice MacBook Pro (Corporate)").first()
    resource = Resource(id="temp-res", name="Temp", enabled=False)
    access_request = AccessRequest(id="req", source_segment="Development")
    risk = create_mock_risk(10)
    policies = db_session.query(Policy).all()
    
    decision = PolicyEvaluator.evaluate_access(user, device, resource, access_request, risk, policies)
    assert decision.decision == PolicyEffect.DENY
    assert "disabled" in decision.reason.lower()

def test_least_privilege_matrix(db_session):
    users = {u.username: u for u in db_session.query(User).all()}
    devices = {d.device_name: d for d in db_session.query(Device).all()}
    resources = {r.name: r for r in db_session.query(Resource).all()}
    policies = db_session.query(Policy).all()

    def eval_access(username, device_name, resource_name, risk_score=10):
        u = users[username]
        d = devices[device_name]
        r = resources[resource_name]
        req = AccessRequest(
            id=str(uuid.uuid4()), user_id=u.id, device_id=d.id, resource_id=r.id,
            network_type=NetworkType.CORPORATE, ip_reputation=IPReputation.TRUSTED,
            is_known_network=True, source_ip="10.0.4.15", source_segment="Development"
        )
        return PolicyEvaluator.evaluate_access(u, d, r, req, create_mock_risk(risk_score), policies).decision

    # Developer
    assert eval_access("alice", "Alice MacBook Pro (Corporate)", "Git Repository") == PolicyEffect.ALLOW
    assert eval_access("alice", "Alice MacBook Pro (Corporate)", "HR Database") == PolicyEffect.DENY
    assert eval_access("alice", "Alice MacBook Pro (Corporate)", "Finance Database") == PolicyEffect.DENY

    # HR
    assert eval_access("bob", "Bob HR Workstation", "HR Database") == PolicyEffect.ALLOW
    assert eval_access("bob", "Bob HR Workstation", "Git Repository") == PolicyEffect.DENY

    # Finance
    assert eval_access("carol", "Carol Finance ThinkPad", "Finance Database") == PolicyEffect.ALLOW
    assert eval_access("carol", "Carol Finance ThinkPad", "HR Database") == PolicyEffect.DENY

    # Vendor
    assert eval_access("vendor-01", "Vendor Contractor Laptop", "HR Database") == PolicyEffect.DENY
    assert eval_access("vendor-01", "Vendor Contractor Laptop", "Git Repository") == PolicyEffect.DENY

    # Admin
    assert eval_access("admin", "Admin Terminal", "Git Repository") == PolicyEffect.ALLOW
    assert eval_access("admin", "Admin Terminal", "HR Database") == PolicyEffect.ALLOW

from app.api.dependencies import get_current_user, require_admin

def test_api_pdp_evaluate_scenarios(admin_client, db_session):
    # Scenario A: Alice, Corp Mac, Git Repo, Low Risk
    req_a = db_session.query(AccessRequest).filter(AccessRequest.source_ip == "10.0.4.15").first()
    res_a = admin_client.post("/api/pdp/evaluate", json={"access_request_id": req_a.id})
    assert res_a.status_code == 200
    assert res_a.json()["decision"] == "ALLOW"

    # Scenario B: Alice, Tablet, Git Repo, Suspicious/Unknown IP
    req_b = db_session.query(AccessRequest).filter(AccessRequest.source_ip == "198.51.100.42").first()
    res_b = admin_client.post("/api/pdp/evaluate", json={"access_request_id": req_b.id})
    assert res_b.status_code == 200
    assert res_b.json()["decision"] == "MFA_REQUIRED"

def test_api_pdp_evaluate_invalid_request(admin_client, db_session):
    res = admin_client.post("/api/pdp/evaluate", json={"access_request_id": "invalid-id"})
    assert res.status_code == 404

def test_api_policies_crud(admin_client, db_session):
    res = admin_client.get("/api/policies")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) > 0
    
    new_policy = {
        "name": "Integration Test Policy",
        "description": "Created during testing",
        "priority": 100,
        "effect": "ALLOW",
        "rules": []
    }
    res_create = admin_client.post("/api/policies", json=new_policy)
    assert res_create.status_code == 201
    policy_id = res_create.json()["id"]

    res_get = admin_client.get(f"/api/policies/{policy_id}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Integration Test Policy"

    res_patch = admin_client.patch(f"/api/policies/{policy_id}", json={"effect": "DENY"})
    assert res_patch.status_code == 200
    assert res_patch.json()["effect"] == "DENY"
    
    res_del = admin_client.delete(f"/api/policies/{policy_id}")
    assert res_del.status_code == 204
    
    res_get_del = admin_client.get(f"/api/policies/{policy_id}")
    assert res_get_del.status_code == 404
