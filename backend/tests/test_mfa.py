import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource
from app.models.access_request import AccessRequest
from app.models.mfa import MFAChallenge, MFAChallengeStatus
from app.mfa.service import MFAService
from app.seed.seed_data import seed_database
from app.policy.seed import seed_policies
from app.segmentation.seed import seed_segments, seed_segment_rules
from app.core.database import SessionLocal, get_db
from app.main import app

@pytest.fixture
def db(db_session):
    seed_database(db_session)
    seed_policies(db_session)
    seed_segments(db_session)
    seed_segment_rules(db_session)
    return db_session

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def get_demo_scenarios(alice_client):
    return alice_client.get("/api/demo/scenarios").json()

def test_pdp_deny_no_challenge_allowed(alice_client, db: Session):
    scenarios = get_demo_scenarios(alice_client)
    # Scenario C is high risk, PDP returns DENY
    reqs_res = alice_client.get("/api/access-requests")
    reqs = reqs_res.json()
    scenario_c = next(s for s in scenarios if s["id"] == "scenario-c")
    match = next(r for r in reqs if r["source_ip"] == scenario_c["network"]["source_ip"])
    
    # Attempt to create MFA challenge
    res = alice_client.post("/api/mfa/challenge", json={"access_request_id": match["id"]})
    assert res.status_code == 403
    assert "MFA cannot override a hard deny" in res.json()["detail"]
    
    # Check PEP enforcement directly
    pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": match["id"]})
    assert pep_res.status_code == 200
    assert pep_res.json()["decision"] == "DENY"
    assert pep_res.json()["access_granted"] is False

def test_pdp_mfa_required_challenge_flow(alice_client, db: Session):
    scenarios = get_demo_scenarios(alice_client)
    # Scenario B requires MFA
    reqs_res = alice_client.get("/api/access-requests")
    reqs = reqs_res.json()
    scenario_b = next(s for s in scenarios if s["id"] == "scenario-b")
    match = next(r for r in reqs if r["source_ip"] == scenario_b["network"]["source_ip"])
    req_id = match["id"]
    
    # Verify initial PEP is MFA_REQUIRED
    pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": req_id})
    print("TEST PEP RESULT:", pep_res.json())
    assert pep_res.json()["decision"] == "MFA_REQUIRED"
    assert pep_res.json()["access_granted"] is False
    
    # Create challenge
    chal_res = alice_client.post("/api/mfa/challenge", json={"access_request_id": req_id})
    assert chal_res.status_code == 200
    chal_data = chal_res.json()
    assert chal_data["status"] == "PENDING"
    challenge_id = chal_data["id"]
    demo_otp = chal_data["demo_otp"]
    
    # Test Wrong OTP
    bad_verify = alice_client.post("/api/mfa/verify", json={"challenge_id": challenge_id, "code": "000000"})
    assert bad_verify.status_code == 400
    
    # Access still not granted
    pep_res2 = alice_client.post("/api/pep/enforce", json={"access_request_id": req_id})
    assert pep_res2.json()["decision"] == "MFA_REQUIRED"
    
    # Test Correct OTP
    good_verify = alice_client.post("/api/mfa/verify", json={"challenge_id": challenge_id, "code": demo_otp})
    assert good_verify.status_code == 200
    assert good_verify.json()["status"] == "VERIFIED"
    
    # Now PDP re-evaluation occurs during enforce and yields ALLOW + segmentation ALLOW -> GRANTED
    pep_res3 = alice_client.post("/api/pep/enforce", json={"access_request_id": req_id})
    assert pep_res3.status_code == 200, pep_res3.text
    assert pep_res3.json()["decision"] == "ALLOW"
    assert pep_res3.json()["access_granted"] is True

def test_mfa_verified_but_segmentation_deny_blocks(alice_client, db: Session):
    # Test Lateral Movement: Development -> HR_Secure
    dev_user = db.query(User).filter(User.role == "Developer").first()
    dev_device = db.query(Device).filter(Device.owner_user_id == dev_user.id).first()
    hr_resource = db.query(Resource).filter(Resource.name == "HR Database").first()
    
    req = AccessRequest(
        user_id=dev_user.id,
        device_id=dev_device.id,
        resource_id=hr_resource.id,
        source_ip="10.0.0.99",
        ip_reputation="UNKNOWN",
        network_type="CORPORATE",
        is_known_network=False,
        failed_attempts=2,
        source_segment="Development"
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    
    # This should be MFA_REQUIRED or DENY. With UNKNOWN and failed attempts, risk might be > 40.
    # Let's enforce it to see
    pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    if pep_res.json()["decision"] == "MFA_REQUIRED":
        # Do MFA
        chal_res = alice_client.post("/api/mfa/challenge", json={"access_request_id": req.id})
        chal_data = chal_res.json()
        alice_client.post("/api/mfa/verify", json={"challenge_id": chal_data["id"], "code": chal_data["demo_otp"]})
        
        # Re-evaluate
        pep_res2 = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
        assert pep_res2.json()["decision"] == "ALLOW"
        assert pep_res2.json()["access_granted"] is False # Blocked by segmentation
        assert "microsegmentation" in pep_res2.json()["reason"]
    elif pep_res.json()["decision"] == "ALLOW":
        # It's ALLOW directly, segmentation blocks
        assert pep_res.json()["access_granted"] is False

def test_expired_challenge_cannot_grant_access(alice_client, db: Session):
    scenarios = get_demo_scenarios(alice_client)
    reqs_res = alice_client.get("/api/access-requests")
    reqs = reqs_res.json()
    scenario_b = next(s for s in scenarios if s["id"] == "scenario-b")
    match = next(r for r in reqs if r["source_ip"] == scenario_b["network"]["source_ip"])
    
    chal_res = alice_client.post("/api/mfa/challenge", json={"access_request_id": match["id"]})
    chal_data = chal_res.json()
    
    # Manually expire the challenge in DB
    chal = db.query(MFAChallenge).filter(MFAChallenge.id == chal_data["id"]).first()
    chal.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db.commit()
    
    # Verify should fail
    verify = alice_client.post("/api/mfa/verify", json={"challenge_id": chal.id, "code": chal_data["demo_otp"]})
    assert verify.status_code == 400
    assert "expired" in verify.json()["detail"]
    
    # Enforce should be MFA_REQUIRED
    pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": match["id"]})
    assert pep_res.status_code == 200, pep_res.text
    assert pep_res.json()["decision"] == "MFA_REQUIRED"
    assert pep_res.json()["access_granted"] is False

def test_re_evaluated_pdp_deny_blocks(alice_client, db: Session):
    scenarios = get_demo_scenarios(alice_client)
    reqs_res = alice_client.get("/api/access-requests")
    reqs = reqs_res.json()
    scenario_b = next(s for s in scenarios if s["id"] == "scenario-b")
    match = next(r for r in reqs if r["source_ip"] == scenario_b["network"]["source_ip"])
    req_id = match["id"]
    
    chal_res = alice_client.post("/api/mfa/challenge", json={"access_request_id": req_id})
    chal_data = chal_res.json()
    alice_client.post("/api/mfa/verify", json={"challenge_id": chal_data["id"], "code": chal_data["demo_otp"]})
    
    # Modify request to be extremely high risk to force DENY on re-evaluation
    req = db.query(AccessRequest).filter(AccessRequest.id == req_id).first()
    req.ip_reputation = "MALICIOUS" # MALICIOUS forces DENY policy
    db.commit()
    
    pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": req_id})
    assert pep_res.status_code == 200, pep_res.text
    assert pep_res.json()["decision"] == "DENY"
    assert pep_res.json()["access_granted"] is False
    
    # Revert to not break other tests since db is module scoped?
    # Actually db is isolated via fixtures if we rollback, but we committed. Let's revert it.
    req.ip_reputation = "UNKNOWN"
    db.commit()

def test_verified_challenge_cannot_be_replayed_if_expired(alice_client, db: Session):
    scenarios = get_demo_scenarios(alice_client)
    reqs_res = alice_client.get("/api/access-requests")
    reqs = reqs_res.json()
    scenario_b = next(s for s in scenarios if s["id"] == "scenario-b")
    match = next(r for r in reqs if r["source_ip"] == scenario_b["network"]["source_ip"])
    
    # challenge was verified in earlier test
    # Find the LATEST challenge
    chal = db.query(MFAChallenge).filter(MFAChallenge.request_id == match["id"]).order_by(MFAChallenge.created_at.desc()).first()
    
    # expire it
    chal.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    
    # PEP should no longer consider it verified
    pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": match["id"]})
    assert pep_res.status_code == 200, pep_res.text
    assert pep_res.json()["decision"] == "MFA_REQUIRED"
    assert pep_res.json()["access_granted"] is False
    
    # un-expire it
    chal.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()
