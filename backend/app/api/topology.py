from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource
from app.models.pep import EnforcementEvent

from app.api.dependencies import get_current_user, require_admin
from app.models.enums import UserRole
from app.risk.service import RiskService

router = APIRouter(prefix="/topology", tags=["Topology"])

@router.get("")
def get_topology(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    users = db.query(User).all()
    devices = db.query(Device).all()
    resources = db.query(Resource).all()
    
    # Filter nodes for normal user
    if current_user.role != UserRole.ADMIN:
        users = [u for u in users if u.id == current_user.id]
        devices = [d for d in devices if d.owner_user_id == current_user.id]
        # Allow normal users to see all resources
    
    # Let's get the latest enforcement event to draw the primary path
    events = db.query(EnforcementEvent).order_by(EnforcementEvent.timestamp.desc()).limit(1).all()
    
    nodes = []
    edges = []
    
    # 1. Add User Nodes
    for u in users:
        nodes.append({"id": f"user_{u.id}", "type": "user", "label": u.username, "metadata": {"role": u.role, "status": u.status}})
        
    # 2. Add Device Nodes
    for d in devices:
        nodes.append({"id": f"device_{d.id}", "type": "device", "label": d.device_name, "metadata": {"posture": d.posture_status, "managed": d.managed}})
        
    # 3. Add PEP Node (Central Hub)
    nodes.append({"id": "pep_gateway", "type": "gateway", "label": "ZeroGate PEP", "metadata": {"Function": "Policy Enforcement Point", "Status": "Active"}})
    
    # 3.5 Add Security Decision Nodes
    nodes.append({"id": "risk_engine", "type": "security", "label": "Risk Engine", "metadata": {"Function": "Context-aware risk evaluation", "Inputs": "Identity, Device, Context", "Outputs": "Risk score & level"}})
    nodes.append({"id": "pdp", "type": "security", "label": "PDP", "metadata": {"Function": "Policy Decision Point", "Decisions": "ALLOW, MFA_REQUIRED, DENY"}})

    # 4. Add Resource & Segment Nodes
    seen_segments = set()
    for r in resources:
        if r.network_segment and r.network_segment not in seen_segments:
            nodes.append({"id": f"segment_{r.network_segment}", "type": "segment", "label": f"{r.network_segment} Segment", "metadata": {"Type": "Microsegment"}})
            seen_segments.add(r.network_segment)
        nodes.append({"id": f"resource_{r.id}", "type": "resource", "label": r.name, "metadata": {"segment": r.network_segment, "enabled": r.enabled}})
        
    # 5. Add Innate User -> Device Edges
    seen_edges = set()
    for d in devices:
        if d.owner_user_id:
            u_id = f"user_{d.owner_user_id}"
            d_id = f"device_{d.id}"
            ud_key = f"{u_id}->{d_id}"
            edges.append({"id": ud_key, "source": u_id, "target": d_id, "status": "inactive"})
            seen_edges.add(ud_key)
            
    # Single source of truth for the latest request
    latest_request_data = None
            
    # Add Edges based on the single latest event
    
    from app.models.access_request import AccessRequest
    for event in events:
        req = db.query(AccessRequest).filter(AccessRequest.id == event.access_request_id).first()
        if not req:
            continue
            
        u_id = f"user_{req.user_id}"
        d_id = f"device_{req.device_id}"
        r_id = f"resource_{req.resource_id}"
        
        # Calculate Risk dynamically for the canonical response
        risk_assessment = RiskService.evaluate_access_request_by_id(req.id, db)
        
        status = "allowed" if event.access_granted else "blocked"
        if event.decision == "MFA_REQUIRED":
            status = "mfa"
            
        latest_request_data = {
            "access_request_id": req.id,
            "user_id": u_id,
            "device_id": d_id,
            "resource_id": r_id,
            "risk_score": risk_assessment.score if risk_assessment else 0,
            "risk_level": risk_assessment.level.value if risk_assessment else "UNKNOWN",
            "pdp_decision": event.decision,
            "pep_status": "ALLOWED" if status == "allowed" else "PENDING MFA" if status == "mfa" else "BLOCKED",
            "segmentation_status": "MICROSEGMENTATION BLOCKED" if event.decision == "DENY" and "microsegmentation" in (event.reason or "").lower() else "ALLOWED" if status == "allowed" else "PENDING" if status == "mfa" else "BLOCKED",
            "reason": event.reason,
            "source_segment": req.source_segment or event.source_segment,
        }
        
        if current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
            continue # Don't draw edges for other users
            
        # Highlight User -> Device
        ud_key = f"{u_id}->{d_id}"
        for e in edges:
            if e["id"] == ud_key:
                e["status"] = "active"
                e["metadata"] = {"is_latest": True}
                
        # Device -> PEP
        dp_key = f"{d_id}->pep_gateway"
        if dp_key not in seen_edges:
            edges.append({"id": dp_key, "source": d_id, "target": "pep_gateway", "status": "active"})
            seen_edges.add(dp_key)
            
        # PEP -> Risk Engine
        pep_risk_key = f"pep_gateway->risk_engine"
        if pep_risk_key not in seen_edges:
            edges.append({"id": pep_risk_key, "source": "pep_gateway", "target": "risk_engine", "status": "active"})
            seen_edges.add(pep_risk_key)
            
        # Risk Engine -> PDP
        risk_pdp_key = f"risk_engine->pdp"
        if risk_pdp_key not in seen_edges:
            edges.append({"id": risk_pdp_key, "source": "risk_engine", "target": "pdp", "status": "active"})
            seen_edges.add(risk_pdp_key)
            
        # PDP -> Segment -> Resource
        segment_id = f"segment_{req.source_segment}" if req.source_segment else f"segment_{event.source_segment}"
        # We fallback to the resource's segment if source_segment is missing
        resource_obj = next((res for res in resources if res.id == req.resource_id), None)
        target_segment_id = f"segment_{resource_obj.network_segment}" if resource_obj and resource_obj.network_segment else "segment_unknown"
        
        latest_request_data["target_segment"] = resource_obj.network_segment if resource_obj else "Unknown"
        
        # If it's a microsegmentation block, we want the edge to go to target_segment_id, but the block happens there
        pdp_seg_key = f"pdp->{target_segment_id}"
        if pdp_seg_key not in seen_edges:
            edges.append({
                "id": pdp_seg_key,
                "source": "pdp",
                "target": target_segment_id,
                "status": status,
                "metadata": {
                    "decision": event.decision,
                    "reason": event.reason
                }
            })
            seen_edges.add(pdp_seg_key)
            
        # Only draw edge from segment to resource if it was actually allowed or MFA (still in progress)
        if status in ["allowed", "mfa"]:
            seg_res_key = f"{target_segment_id}->{r_id}"
            if seg_res_key not in seen_edges:
                edges.append({
                    "id": seg_res_key,
                    "source": target_segment_id,
                    "target": r_id,
                    "status": status,
                    "metadata": {
                        "decision": event.decision
                    }
                })
                seen_edges.add(seg_res_key)
            
    return {
        "nodes": nodes,
        "edges": edges,
        "latest_request": latest_request_data
    }
