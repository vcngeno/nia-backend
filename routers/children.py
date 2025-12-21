"""
Children Management Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from models import Child, GradeLevel, Language
from auth import get_current_user_id
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ChildCreate(BaseModel):
    name: str
    age: int
    grade_level: GradeLevel
    pin: str
    language: Optional[Language] = Language.ENGLISH
    has_autism: Optional[bool] = False
    has_dyslexia: Optional[bool] = False
    has_adhd: Optional[bool] = False
    is_visual_learner: Optional[bool] = False
    use_simplified_language: Optional[bool] = False


class ChildResponse(BaseModel):
    id: int
    name: str
    age: int
    grade_level: str
    language: str
    has_autism: bool
    has_dyslexia: bool
    has_adhd: bool
    is_visual_learner: bool
    use_simplified_language: bool
    
    class Config:
        from_attributes = True


class ChildPINLogin(BaseModel):
    child_id: int
    pin: str


@router.post("/", response_model=ChildResponse)
async def create_child(
    child_data: ChildCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new child profile"""
    
    if len(child_data.pin) != 4 or not child_data.pin.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN must be exactly 4 digits"
        )
    
    new_child = Child(
        parent_id=user_id,
        name=child_data.name,
        age=child_data.age,
        grade_level=child_data.grade_level,
        pin=child_data.pin,
        language=child_data.language,
        has_autism=child_data.has_autism,
        has_dyslexia=child_data.has_dyslexia,
        has_adhd=child_data.has_adhd,
        is_visual_learner=child_data.is_visual_learner,
        use_simplified_language=child_data.use_simplified_language
    )
    
    db.add(new_child)
    await db.commit()
    await db.refresh(new_child)
    
    logger.info(f"New child profile created: {child_data.name}")
    
    return new_child


@router.get("/", response_model=List[ChildResponse])
async def get_children(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all children for the logged-in parent"""
    
    result = await db.execute(
        select(Child).where(Child.parent_id == user_id)
    )
    children = result.scalars().all()
    
    return children


@router.post("/login")
async def child_pin_login(
    login_data: ChildPINLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate child with PIN"""
    
    result = await db.execute(
        select(Child).where(Child.id == login_data.child_id)
    )
    child = result.scalar_one_or_none()
    
    if not child or child.pin != login_data.pin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )
    
    logger.info(f"Child logged in: {child.name}")
    
    return {
        "success": True,
        "child": {
            "id": child.id,
            "name": child.name,
            "grade_level": child.grade_level.value
        }
    }
