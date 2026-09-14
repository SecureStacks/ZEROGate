from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.context import DemoScenarioSchema
from app.seed.seed_data import get_demo_scenarios, seed_database

from app.api.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/demo", tags=["Demo"])

@router.get("/scenarios", response_model=List[DemoScenarioSchema])
def list_demo_scenarios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve the deterministic demo context scenarios for testing and simulation."""
    return get_demo_scenarios(db)

@router.post("/seed", status_code=status.HTTP_200_OK)
def trigger_seed(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Initialize or refresh the deterministic seed database entities."""
    seed_database(db)
    return {
        "status": "success",
        "message": "ZeroGate demo database seeded successfully"
    }
