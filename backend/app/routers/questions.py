from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import QuestionQueue
from app.schemas import QuestionResponse
from pydantic import BaseModel

router = APIRouter()


class QuestionStatusUpdate(BaseModel):
    status: str  # "pending" | "asked" | "dismissed"


@router.get("/", response_model=list[QuestionResponse])
async def list_questions(
    user_id: int = None,
    session_id: int = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List questions with optional filters"""
    query = db.query(QuestionQueue)
    
    if user_id:
        query = query.filter(QuestionQueue.user_id == user_id)
    if session_id:
        query = query.filter(QuestionQueue.session_id == session_id)
    if status:
        query = query.filter(QuestionQueue.status == status)
    
    questions = query.order_by(QuestionQueue.created_at.desc()).all()
    return questions


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: Session = Depends(get_db)):
    """Get question by ID"""
    question = db.query(QuestionQueue).filter(QuestionQueue.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.patch("/{question_id}/status")
async def update_question_status(
    question_id: int,
    update: QuestionStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update question status"""
    question = db.query(QuestionQueue).filter(QuestionQueue.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if update.status not in ["pending", "asked", "dismissed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    question.status = update.status
    db.commit()
    db.refresh(question)
    
    return question
