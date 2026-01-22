from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Session as DBSession, Message, User
from app.schemas import MessageCreate, MessageResponse, SessionResponse
from app.service import ProcessingService

router = APIRouter()


class SessionCreate(BaseModel):
    user_id: int = None


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(db: Session = Depends(get_db)):
    """List all sessions"""
    sessions = db.query(DBSession).all()
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get session by ID"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate = None,
    user_id: int = Query(None),
    db: Session = Depends(get_db)
):
    """Create a new session"""
    # Get user_id from query param or body
    target_user_id = user_id or (session_data.user_id if session_data else None)
    
    # If no user_id provided, use first user or create one
    if target_user_id is None:
        user = db.query(User).first()
        if not user:
            user = User(name="Default User", locale="en")
            db.add(user)
            db.commit()
            db.refresh(user)
        target_user_id = user.id
    else:
        user = db.query(User).filter(User.id == target_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    session = DBSession(user_id=target_user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def get_session_messages(session_id: int, db: Session = Depends(get_db)):
    """Get all messages for a session"""
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
    return messages


@router.post("/{session_id}/messages", response_model=dict)
async def create_message(
    session_id: int,
    message: MessageCreate,
    extractor_version: str = Query("v3"),
    planner_version: str = Query("v1"),
    db: Session = Depends(get_db)
):
    """Process a new message through the AI pipeline"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    service = ProcessingService(db)
    result = await service.process_message(
        session_id, message.text, extractor_version, planner_version
    )
    return result
