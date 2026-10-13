"""
Database Models for Nia Learning Assistant
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class GradeLevel(str, enum.Enum):
    """Grade levels for children"""
    KINDERGARTEN = "kindergarten"
    GRADE_1 = "1st"
    GRADE_2 = "2nd"
    GRADE_3 = "3rd"
    GRADE_4 = "4th"
    GRADE_5 = "5th"
    GRADE_6 = "6th"
    GRADE_7 = "7th"
    GRADE_8 = "8th"
    GRADE_9 = "9th"
    GRADE_10 = "10th"
    GRADE_11 = "11th"
    GRADE_12 = "12th"


class Language(str, enum.Enum):
    """Supported languages"""
    ENGLISH = "english"
    SPANISH = "spanish"


class FolderCategory(str, enum.Enum):
    """Conversation folder categories"""
    MATH = "Math"
    SCIENCE = "Science"
    ENGLISH = "English"
    HISTORY = "History"
    GEOGRAPHY = "Geography"
    TRAVEL = "Travel"
    GENERAL = "General"


class User(Base):
    """Parent/Guardian accounts"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")


class Child(Base):
    """Child profiles managed by parents"""
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    grade_level = Column(Enum(GradeLevel), nullable=False)
    pin_hash = Column(String(255), nullable=False)
    
    language = Column(Enum(Language), default=Language.ENGLISH)
    has_autism = Column(Boolean, default=False)
    has_dyslexia = Column(Boolean, default=False)
    has_adhd = Column(Boolean, default=False)
    is_visual_learner = Column(Boolean, default=False)
    use_simplified_language = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent = relationship("User", back_populates="children")
    conversations = relationship("Conversation", back_populates="child", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation threads with automatic folder categorization"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    title = Column(String, nullable=False)
    folder = Column(Enum(FolderCategory), default=FolderCategory.GENERAL)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    child = relationship("Child", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    depth_level = Column(Integer, default=1)
    source_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")


class EducationalContent(Base):
    """Curated educational content for RAG system"""
    __tablename__ = "educational_content"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    grade_level = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    file_path = Column(String, unique=True, nullable=False)
    content_hash = Column(String, nullable=False)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
