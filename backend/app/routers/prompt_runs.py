from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PromptRun, Session as DBSession
from app.schemas import PromptRunResponse

router = APIRouter()


@router.get("/", response_model=list[PromptRunResponse])
async def list_prompt_runs(
    session_id: int = Query(None),
    user_id: int = Query(None),
    prompt_name: str = Query(None),
    parse_ok: bool = Query(None),
    model: str = Query(None),
    db: Session = Depends(get_db)
):
    """List prompt runs with filters"""
    query = db.query(PromptRun)
    
    if session_id:
        query = query.filter(PromptRun.session_id == session_id)
    elif user_id:
        # Filter by user_id through sessions
        user_sessions = db.query(DBSession.id).filter(DBSession.user_id == user_id).all()
        session_ids = [s.id for s in user_sessions]
        if session_ids:
            query = query.filter(PromptRun.session_id.in_(session_ids))
        else:
            # No sessions for this user, return empty
            return []
    
    if prompt_name:
        query = query.filter(PromptRun.prompt_name == prompt_name)
    if parse_ok is not None:
        query = query.filter(PromptRun.parse_ok == parse_ok)
    if model:
        query = query.filter(PromptRun.model == model)
    
    runs = query.order_by(PromptRun.created_at.desc()).all()
    return runs


@router.get("/{run_id}", response_model=PromptRunResponse)
async def get_prompt_run(run_id: int, db: Session = Depends(get_db)):
    """Get prompt run by ID"""
    run = db.query(PromptRun).filter(PromptRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Prompt run not found")
    return run
