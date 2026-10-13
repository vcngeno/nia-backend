"""
Children Management Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from database import get_db
from models import Child, GradeLevel, Language
from auth import (
    create_access_token,
    get_current_user_id,
    hash_password,
    verify_password,
)
from config import settings
from datetime import timedelta
from rate_limit import rate_limit_pin_login
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ChildCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=3, le=18)
    grade_level: GradeLevel
    pin: str = Field(pattern=r"^[0-9]{4}$")
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
    pin: str = Field(pattern=r"^[0-9]{4}$")


@router.post("/", response_model=ChildResponse)
async def create_child(
    child_data: ChildCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new child profile"""
    
    new_child = Child(
        parent_id=user_id,
        name=child_data.name,
        age=child_data.age,
        grade_level=child_data.grade_level,
        pin_hash=hash_password(child_data.pin),
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
    _: None = Depends(rate_limit_pin_login),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate child with PIN"""
    
    result = await db.execute(
        select(Child).where(Child.id == login_data.child_id)
    )
    child = result.scalar_one_or_none()
    
    if not child or not verify_password(login_data.pin, child.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )
    
    logger.info(f"Child logged in: {child.name}")

    access_token = create_access_token(
        data={"child_id": child.id, "token_type": "child"},
        expires_delta=timedelta(minutes=settings.CHILD_TOKEN_EXPIRE_MINUTES),
    )
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "child": {
            "id": child.id,
            "name": child.name,
            "grade_level": child.grade_level.value
        }
    }
