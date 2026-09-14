from sqlalchemy.orm import Session
from app.models.segmentation import SegmentRule
from app.segmentation.schemas import SegmentDecision

class SegmentationEvaluator:
    @staticmethod
    def check_segment_access(db: Session, source_segment: str, destination_segment: str) -> SegmentDecision:
        if not source_segment or not destination_segment:
            return SegmentDecision(
                allowed=False,
                source_segment=source_segment or "Unknown",
                destination_segment=destination_segment or "Unknown",
                matched_rule=None,
                reason="Source or destination segment missing. Default deny."
            )
            
        rules = db.query(SegmentRule).filter(
            SegmentRule.enabled == True,
            SegmentRule.source_segment == source_segment,
            SegmentRule.destination_segment == destination_segment
        ).order_by(SegmentRule.priority.asc(), SegmentRule.id.asc()).all()
        
        if not rules:
            return SegmentDecision(
                allowed=False,
                source_segment=source_segment,
                destination_segment=destination_segment,
                matched_rule=None,
                reason=f"No matching segmentation rule for {source_segment} -> {destination_segment}. Default deny."
            )
            
        matched_rule = rules[0]
        return SegmentDecision(
            allowed=matched_rule.allowed,
            source_segment=source_segment,
            destination_segment=destination_segment,
            matched_rule=matched_rule.description or f"Rule ID: {matched_rule.id}",
            reason=f"Matched priority {matched_rule.priority} rule allowing traffic." if matched_rule.allowed else f"Matched priority {matched_rule.priority} rule blocking traffic."
        )
