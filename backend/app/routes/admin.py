from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import InterviewTemplate, InterviewTemplateCreate, InterviewTemplateUpdate, InterviewTemplateResponse
from ..services.llm_service import llm_service

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/templates", response_model=List[InterviewTemplateResponse])
def get_templates(db: Session = Depends(get_db)):
    return db.query(InterviewTemplate).filter(InterviewTemplate.is_active == True).all()

@router.post("/templates", response_model=InterviewTemplateResponse)
def create_template(template: InterviewTemplateCreate, db: Session = Depends(get_db)):
    db_template = InterviewTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.put("/templates/{template_id}", response_model=InterviewTemplateResponse)
def update_template(template_id: int, template: InterviewTemplateUpdate, db: Session = Depends(get_db)):
    db_template = db.query(InterviewTemplate).filter(InterviewTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template.dict(exclude_unset=True).items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    db_template = db.query(InterviewTemplate).filter(InterviewTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_template.is_active = False
    db.commit()
    return {"message": "Template deleted successfully"}

@router.post("/generate-template")
async def generate_template_from_goals(request: dict, db: Session = Depends(get_db)):
    goals = request.get("goals", "")
    if not goals:
        raise HTTPException(status_code=400, detail="Goals are required")
        
    try:
        questions_schema = await llm_service.generate_questions_from_goals(goals)
        
        template_data = InterviewTemplateCreate(
            name=f"Generated Template - {goals[:50]}...",
            description=f"Auto-generated template based on: {goals}",
            questions_schema=questions_schema
        )
        
        db_template = InterviewTemplate(**template_data.dict())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        return db_template
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")

@router.get("/templates/{template_id}", response_model=InterviewTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(InterviewTemplate).filter(InterviewTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template