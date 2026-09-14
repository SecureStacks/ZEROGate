from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserRead, UserCreate

from app.api.dependencies import get_current_user, require_admin
from app.models.enums import UserRole

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[UserRead])
def list_users(
    role: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all simulated users with optional role and status filters."""
    query = db.query(User)
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(User.id == current_user.id)
    else:
        if role:
            query = query.filter(User.role == role)
        if status_filter:
            query = query.filter(User.status == status_filter)
            
    return query.order_by(User.username).all()

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve a single user by ID."""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found"
        )
    return user
