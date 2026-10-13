"""
Conversation & Chat Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, or_, select
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from database import get_db
from models import Conversation, Message, Child, FolderCategory
from auth import get_current_actor
from rate_limit import rate_limit_chat
from services.rag_service import RAGService
from services.conversation_service import ConversationService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    child_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[int] = Field(default=None, gt=0)
    depth_level: int = Field(default=1, ge=1, le=5)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    depth_level: int
    source_type: Optional[str]
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    title: str
    folder: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/message")
async def send_message(
    chat_data: ChatMessage,
    actor: dict = Depends(get_current_actor),
    _: None = Depends(rate_limit_chat),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get AI response"""
    
    result = await db.execute(
        select(Child).where(
            Child.id == chat_data.child_id,
            or_(
                Child.parent_id == actor.get("user_id"),
                Child.id == actor.get("child_id"),
            )
        )
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    conversation = None
    if chat_data.conversation_id is not None:
        result = await db.execute(
            select(Conversation)
            .join(Child)
            .where(
                Conversation.id == chat_data.conversation_id,
                Conversation.child_id == chat_data.child_id,
                or_(
                    Child.parent_id == actor.get("user_id"),
                    Child.id == actor.get("child_id"),
                )
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    if not conversation:
        title = ConversationService.generate_title(chat_data.message)
        folder = ConversationService.categorize_conversation(title, chat_data.message)
        
        conversation = Conversation(
            child_id=chat_data.child_id,
            title=title,
            folder=folder
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    history_messages = result.scalars().all()
    
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_messages
    ]
    
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_data.message,
        depth_level=chat_data.depth_level
    )
    db.add(user_message)
    await db.commit()
    
    ai_response, source_type = await RAGService.get_ai_response(
        question=chat_data.message,
        child=child,
        conversation_history=conversation_history,
        depth_level=chat_data.depth_level,
        db=db
    )
    
    ai_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_response,
        depth_level=chat_data.depth_level,
        source_type=source_type
    )
    db.add(ai_message)
    await db.commit()
    await db.refresh(ai_message)
    
    return {
        "conversation_id": conversation.id,
        "message": MessageResponse.from_orm(ai_message)
    }


@router.get("/folders/{child_id}")
async def get_folders(
    child_id: int,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation folders with counts"""
    
    result = await db.execute(
        select(Conversation)
        .join(Child)
        .where(
            Conversation.child_id == child_id,
            or_(
                Child.parent_id == actor.get("user_id"),
                Child.id == actor.get("child_id"),
            )
        )
    )
    conversations = result.scalars().all()
    
    folder_counts = {}
    for conv in conversations:
        folder = conv.folder.value
        folder_counts[folder] = folder_counts.get(folder, 0) + 1
    
    return {"folders": folder_counts}


@router.get("/conversations/{child_id}")
async def get_conversations(
    child_id: int,
    folder: Optional[FolderCategory] = None,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db)
):
    """Get conversations for a child, optionally filtered by folder"""
    
    query = (
        select(Conversation)
        .join(Child)
        .where(
            Conversation.child_id == child_id,
            or_(
                Child.parent_id == actor.get("user_id"),
                Child.id == actor.get("child_id"),
            )
        )
    )
    
    if folder:
        query = query.where(Conversation.folder == folder)
    
    query = query.order_by(desc(Conversation.updated_at))
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return {
        "conversations": [
            ConversationResponse.from_orm(conv) for conv in conversations
        ]
    }


@router.get("/messages/{conversation_id}")
async def get_messages(
    conversation_id: int,
    actor: dict = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a conversation"""

    result = await db.execute(
        select(Conversation)
        .join(Child)
        .where(
            Conversation.id == conversation_id,
            or_(
                Child.parent_id == actor.get("user_id"),
                Child.id == actor.get("child_id"),
            )
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return {
        "messages": [MessageResponse.from_orm(msg) for msg in messages]
    }
