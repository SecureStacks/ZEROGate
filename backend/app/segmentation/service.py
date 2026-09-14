from sqlalchemy.orm import Session
from app.models.segmentation import Microsegment, SegmentRule
from app.segmentation.schemas import MicrosegmentCreate, SegmentRuleCreate, SegmentRuleUpdate
from typing import List

class SegmentationService:
    @staticmethod
    def get_segments(db: Session) -> List[Microsegment]:
        return db.query(Microsegment).all()
        
    @staticmethod
    def get_segment_rules(db: Session) -> List[SegmentRule]:
        return db.query(SegmentRule).order_by(SegmentRule.priority.asc()).all()
        
    @staticmethod
    def create_segment_rule(db: Session, rule_in: SegmentRuleCreate) -> SegmentRule:
        rule = SegmentRule(**rule_in.model_dump())
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule
        
    @staticmethod
    def get_segment_rule(db: Session, rule_id: str) -> SegmentRule:
        return db.query(SegmentRule).filter(SegmentRule.id == rule_id).first()
        
    @staticmethod
    def update_segment_rule(db: Session, rule_id: str, rule_in: SegmentRuleUpdate) -> SegmentRule:
        rule = db.query(SegmentRule).filter(SegmentRule.id == rule_id).first()
        if not rule:
            return None
            
        update_data = rule_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
            
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule
        
    @staticmethod
    def delete_segment_rule(db: Session, rule_id: str) -> bool:
        rule = db.query(SegmentRule).filter(SegmentRule.id == rule_id).first()
        if not rule:
            return False
            
        db.delete(rule)
        db.commit()
        return True
