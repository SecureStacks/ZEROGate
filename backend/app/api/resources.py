from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.resource import Resource
from app.schemas.resource import ResourceRead

from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/resources", tags=["Resources"])

@router.get("", response_model=List[ResourceRead])
def list_resources(
    segment: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all protected resources with optional segment and enabled filters."""
    query = db.query(Resource)
    if segment:
        query = query.filter(Resource.network_segment == segment)
    if enabled is not None:
        query = query.filter(Resource.enabled == enabled)
    return query.order_by(Resource.name).all()

@router.get("/{resource_id}", response_model=ResourceRead)
def get_resource(resource_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve a single protected resource by ID."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with ID '{resource_id}' not found"
        )
    return resource
