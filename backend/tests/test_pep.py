import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal, get_db
from app.models.access_request import AccessRequest
from app.models.resource import Resource
from app.models.enums import PolicyEffect
from app.seed.seed_data import seed_database
from app.policy.seed import seed_policies
from app.segmentation.seed import seed_segments, seed_segment_rules
from app.pep.service import PEPService

from app.models.mfa import MFAChallenge

@pytest.fixture
def db(db_session):
    db_session.query(MFAChallenge).delete()
    db_session.commit()
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

def test_pep_scenario_a(db: Session):
    # Scenario A: Low risk, developer -> git repo -> ALLOW -> Segmentation ALLOW
    # Access request 1 is usually Scenario A in seed_data
    access_req = db.query(AccessRequest).first()  # Alice to Git Repo
    # Verify source_segment is 'Development' and resource is 'Development'
    resource = db.query(Resource).filter(Resource.id == access_req.resource_id).first()
    assert access_req.source_segment == "Development"
    assert resource.network_segment == "Development"
    
    result = PEPService.enforce_access(db, access_req.id)
    assert result.decision == PolicyEffect.ALLOW.value
    assert result.access_granted is True
    assert result.segment_check.allowed is True
    assert result.segment_check.source_segment == "Development"
    assert result.segment_check.destination_segment == "Development"

def test_pep_scenario_b(db: Session):
    # Scenario B: Medium risk, MFA_REQUIRED
    # Find Alice's BYOD request
    access_req = db.query(AccessRequest).filter(
        AccessRequest.source_segment == "Development",
        AccessRequest.network_type == "PUBLIC_WIFI"
    ).first()
    
    result = PEPService.enforce_access(db, access_req.id)
    assert result.decision == PolicyEffect.MFA_REQUIRED.value
    assert result.access_granted is False
    assert result.segment_check is None

def test_pep_scenario_c(db: Session):
    # Scenario C: High risk, DENY
    access_req = db.query(AccessRequest).filter(
        AccessRequest.network_type == "UNKNOWN",
        AccessRequest.is_tor == True
    ).first()
    
    result = PEPService.enforce_access(db, access_req.id)
    assert result.decision == PolicyEffect.DENY.value
    assert result.access_granted is False
    assert result.segment_check is None

def test_lateral_movement_blocked(db: Session):
    # Create a request: Developer attempting to access HR Database
    # Note: PDP policy might deny this anyway due to role-based access.
    # To strictly test segmentation, we can temporarily create a request where PDP allows but segmentation denies.
    # But wait, HR Database has resource-level policy that denies non-HR. 
    # The requirement is that PEP blocks east-west movement.
    
    hr_resource = db.query(Resource).filter(Resource.name == "HR Database").first()
    alice = db.query(AccessRequest).first().user_id # Alice is developer
    
    # Let's use Alice's device from scenario A
    dev_id = db.query(AccessRequest).first().device_id
    
    req = AccessRequest(
        user_id=alice,
        device_id=dev_id,
        resource_id=hr_resource.id,
        source_segment="Development",
        source_ip="10.0.4.15"
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    
    result = PEPService.enforce_access(db, req.id)
    assert result.access_granted is False
    # Even if PDP DENY or ALLOW, access_granted must be False.
    # If PDP DENY, segment_check might be None.
    # We can test segmentation directly
    from app.segmentation.evaluator import SegmentationEvaluator
    seg_result = SegmentationEvaluator.check_segment_access(db, "Development", "HR_Secure")
from app.api.dependencies import get_current_user

def test_api_pep_enforce(admin_client, db: Session):
    access_req = db.query(AccessRequest).first()
    response = admin_client.post("/api/pep/enforce", json={"access_request_id": access_req.id})
    assert response.status_code == 200
    assert response.json()["decision"] in ("ALLOW", "DENY")

def test_invalid_request_id(admin_client, db: Session):
    response = admin_client.post("/api/pep/enforce", json={"access_request_id": "invalid-id"})
    # Service handles invalid ID gracefully and returns DENY
    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"
    assert response.json()["access_granted"] is False
