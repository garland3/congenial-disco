from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

Base = declarative_base()

class InterviewTemplate(Base):
    __tablename__ = "interview_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    questions_schema = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, nullable=False)
    session_data = Column(JSON)
    conversation_history = Column(JSON, default=list)
    current_question_index = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    awaiting_confirmation = Column(Boolean, default=False)
    extracted_data = Column(JSON, default=dict)
    field_scores = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class InterviewTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    questions_schema: Dict[str, Any]

class InterviewTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    questions_schema: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class InterviewTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    questions_schema: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True

class InterviewSessionCreate(BaseModel):
    template_id: int

class InterviewSessionResponse(BaseModel):
    id: int
    template_id: int
    session_data: Optional[Dict[str, Any]]
    conversation_history: Optional[List[Dict[str, Any]]] = []
    current_question_index: int
    is_completed: bool
    awaiting_confirmation: bool = False
    extracted_data: Optional[Dict[str, Any]] = {}
    field_scores: Optional[Dict[str, Any]] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    is_complete: bool
    awaiting_confirmation: bool = False
    extracted_data: Optional[Dict[str, Any]] = None
    field_scores: Optional[Dict[str, Any]] = None
    session_data: Optional[Dict[str, Any]] = None