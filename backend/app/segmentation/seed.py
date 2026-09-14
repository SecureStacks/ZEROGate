from sqlalchemy.orm import Session
from app.models.segmentation import Microsegment, SegmentRule

def seed_segments(db: Session):
    existing = {s.name for s in db.query(Microsegment).all()}
    segments = [
        {"name": "Development", "description": "Developer workstations and non-prod services"},
        {"name": "HR_Secure", "description": "Human Resources systems and data"},
        {"name": "Finance_Core", "description": "Financial ledger and payroll systems"},
        {"name": "Cloud_Admin", "description": "Cloud infrastructure and orchestration"},
        {"name": "API_Gateway", "description": "Core business backend APIs"}
    ]
    for seg in segments:
        if seg["name"] not in existing:
            db.add(Microsegment(**seg))
    db.commit()

def seed_segment_rules(db: Session):
    rules = [
        # RULE 1
        {"source_segment": "Development", "destination_segment": "Development", "allowed": True, "description": "Developers may communicate with development resources.", "priority": 10},
        # RULE 2
        {"source_segment": "Development", "destination_segment": "HR_Secure", "allowed": False, "description": "Prevent developer lateral movement into HR systems.", "priority": 10},
        # RULE 3
        {"source_segment": "Development", "destination_segment": "Finance_Core", "allowed": False, "description": "Prevent developer lateral movement into Finance systems.", "priority": 10},
        # RULE 4
        {"source_segment": "Development", "destination_segment": "Cloud_Admin", "allowed": False, "description": "Development resources cannot directly reach cloud administration.", "priority": 10},
        # RULE 5
        {"source_segment": "HR_Secure", "destination_segment": "HR_Secure", "allowed": True, "description": "HR internal access", "priority": 10},
        # RULE 6
        {"source_segment": "HR_Secure", "destination_segment": "Finance_Core", "allowed": False, "description": "Prevent HR to Finance lateral movement", "priority": 10},
        # RULE 7
        {"source_segment": "Finance_Core", "destination_segment": "Finance_Core", "allowed": True, "description": "Finance internal access", "priority": 10},
        # RULE 8
        {"source_segment": "Finance_Core", "destination_segment": "HR_Secure", "allowed": False, "description": "Prevent Finance to HR lateral movement", "priority": 10},
        # RULE 9
        {"source_segment": "Cloud_Admin", "destination_segment": "Cloud_Admin", "allowed": True, "description": "Admin internal access", "priority": 10},
        # RULE 10
        {"source_segment": "API_Gateway", "destination_segment": "Development", "allowed": True, "description": "API Gateway to Dev backend", "priority": 10},
        # RULE 11
        {"source_segment": "API_Gateway", "destination_segment": "HR_Secure", "allowed": False, "description": "API Gateway blocked from HR", "priority": 10},
        # RULE 12
        {"source_segment": "API_Gateway", "destination_segment": "Finance_Core", "allowed": False, "description": "API Gateway blocked from Finance", "priority": 10}
    ]
    
    existing = {(r.source_segment, r.destination_segment): r for r in db.query(SegmentRule).all()}
    for rule in rules:
        if (rule["source_segment"], rule["destination_segment"]) not in existing:
            db.add(SegmentRule(**rule))
            
    db.commit()
