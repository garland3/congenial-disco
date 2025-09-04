from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import (
    InterviewTemplate, InterviewSession, InterviewSessionCreate, 
    InterviewSessionResponse, ChatMessage, ChatResponse, InterviewTemplateResponse
)
from ..services.llm_service import llm_service

router = APIRouter(prefix="/api/interview", tags=["interview"])

@router.get("/templates", response_model=List[InterviewTemplateResponse])
def get_available_templates(db: Session = Depends(get_db)):
    return db.query(InterviewTemplate).filter(InterviewTemplate.is_active == True).all()

@router.post("/start/{template_id}", response_model=InterviewSessionResponse)
def start_interview(template_id: int, db: Session = Depends(get_db)):
    template = db.query(InterviewTemplate).filter(
        InterviewTemplate.id == template_id,
        InterviewTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    session = InterviewSession(
        template_id=template_id,
        session_data={},
        conversation_history=[],
        current_question_index=0,
        awaiting_confirmation=False,
        extracted_data={},
        field_scores={}
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session

@router.get("/session/{session_id}", response_model=InterviewSessionResponse)
def get_interview_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/session/{session_id}/chat", response_model=ChatResponse)
async def chat_with_session(session_id: int, message: ChatMessage, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.is_completed:
        return ChatResponse(
            response="This interview has already been completed.",
            is_complete=True,
            session_data=session.session_data
        )
    
    template = db.query(InterviewTemplate).filter(InterviewTemplate.id == session.template_id).first()
    questions_schema = template.questions_schema
    
    # Initialize conversation history if needed
    if session.conversation_history is None:
        session.conversation_history = []
    
    # Add user message to conversation history
    session.conversation_history.append({
        "sender": "user",
        "text": message.message
    })
    
    # Check if user is confirming extracted data
    if session.awaiting_confirmation:
        confirm_phrases = ['yes', 'correct', 'looks good', 'that\'s right', 'confirm', 'approve']
        reject_phrases = ['no', 'incorrect', 'wrong', 'not right', 'reject', 'change']
        
        if any(phrase in message.message.lower().strip() for phrase in confirm_phrases):
            # User confirmed - complete the interview
            session.is_completed = True
            session.session_data = session.extracted_data or {}
            
            # Add confirmation to conversation
            confirmation_msg = "Perfect! Thank you for confirming. Your interview is now complete."
            session.conversation_history.append({
                "sender": "assistant", 
                "text": confirmation_msg
            })
            
            db.commit()
            return ChatResponse(
                response=confirmation_msg,
                is_complete=True,
                session_data=session.session_data
            )
        elif any(phrase in message.message.lower().strip() for phrase in reject_phrases):
            # User wants changes - continue the interview
            session.awaiting_confirmation = False
            continue_msg = "I understand. Let's continue our conversation to gather more accurate information. What would you like to clarify or add?"
            session.conversation_history.append({
                "sender": "assistant",
                "text": continue_msg
            })
            db.commit()
            return ChatResponse(
                response=continue_msg,
                is_complete=False
            )
    
    # Check if this is the very first interaction
    if len(session.conversation_history) == 1:  # Only user's first message
        ready_phrases = ['ready', 'ok', 'yes', 'start', 'lets start', 'let\'s start', 'ok. lets start', 'begin']
        if any(phrase in message.message.lower().strip() for phrase in ready_phrases):
            welcome_msg = "Great! I'll be conducting this interview with you. Let's have a natural conversation, and I'll gather the information we need. Tell me, what brings you here today?"
        else:
            welcome_msg = "Hello! Welcome to your interview session. I will ask you questions through a natural conversation. Let me know when you're ready to begin!"
        
        session.conversation_history.append({
            "sender": "assistant",
            "text": welcome_msg
        })
        db.commit()
        return ChatResponse(response=welcome_msg, is_complete=False)
    
    # Extract data from conversation so far
    extracted_data = await llm_service.extract_data_from_conversation(
        session.conversation_history[:-1],  # Exclude the current message we haven't processed yet
        questions_schema
    )
    
    # Judge completeness using the LLM judge
    field_scores, overall_complete, suggestions = await llm_service.judge_completeness(
        extracted_data, questions_schema
    )
    
    # Update session with latest extracted data and scores
    session.extracted_data = extracted_data
    session.field_scores = field_scores
    
    if overall_complete:
        # Prepare confirmation message
        confirmation_msg = "Thank you for sharing all that information! Let me summarize what I've gathered:\n\n"
        for field_name, value in extracted_data.items():
            if value:
                confirmation_msg += f"• **{field_name.replace('_', ' ').title()}**: {value}\n"
        confirmation_msg += "\nDoes this look accurate? Please confirm if this is correct, or let me know what needs to be changed."
        
        session.awaiting_confirmation = True
        session.conversation_history.append({
            "sender": "assistant",
            "text": confirmation_msg
        })
        
        db.commit()
        return ChatResponse(
            response=confirmation_msg,
            is_complete=False,
            awaiting_confirmation=True,
            extracted_data=extracted_data,
            field_scores=field_scores
        )
    else:
        # Generate next question based on what's missing
        next_question = await llm_service.generate_next_question(
            session.conversation_history,
            questions_schema,
            extracted_data,
            field_scores,
            suggestions
        )
        
        session.conversation_history.append({
            "sender": "assistant",
            "text": next_question
        })
        
        db.commit()
        return ChatResponse(
            response=next_question,
            is_complete=False,
            extracted_data=extracted_data,
            field_scores=field_scores
        )

@router.get("/session/{session_id}/status")
def get_session_status(session_id: int, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    template = db.query(InterviewTemplate).filter(InterviewTemplate.id == session.template_id).first()
    
    total_questions = len(template.questions_schema) if template.questions_schema else 0
    
    return {
        "session_id": session.id,
        "current_question": session.current_question_index + 1,
        "total_questions": total_questions,
        "is_completed": session.is_completed,
        "progress_percentage": round((session.current_question_index / total_questions) * 100) if total_questions > 0 else 0
    }