from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.segmentation.schemas import MicrosegmentSchema, SegmentRuleSchema, SegmentRuleCreate, SegmentRuleUpdate
from app.segmentation.service import SegmentationService

from app.api.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(tags=["segmentation"])

@router.get("/segments", response_model=List[MicrosegmentSchema])
def get_segments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SegmentationService.get_segments(db)

@router.get("/segment-rules", response_model=List[SegmentRuleSchema])
def get_segment_rules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SegmentationService.get_segment_rules(db)

@router.post("/segment-rules", response_model=SegmentRuleSchema)
def create_segment_rule(rule_in: SegmentRuleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SegmentationService.create_segment_rule(db, rule_in)

@router.get("/segment-rules/{rule_id}", response_model=SegmentRuleSchema)
def get_segment_rule(rule_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = SegmentationService.get_segment_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Segment rule not found")
    return rule

@router.patch("/segment-rules/{rule_id}", response_model=SegmentRuleSchema)
def update_segment_rule(rule_id: str, rule_in: SegmentRuleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = SegmentationService.update_segment_rule(db, rule_id, rule_in)
    if not rule:
        raise HTTPException(status_code=404, detail="Segment rule not found")
    return rule

@router.delete("/segment-rules/{rule_id}")
def delete_segment_rule(rule_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = SegmentationService.delete_segment_rule(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Segment rule not found")
    return {"status": "success"}
