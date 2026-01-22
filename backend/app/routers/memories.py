from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Memory
from app.schemas import MemoryResponse

router = APIRouter()


@router.get("/", response_model=list[MemoryResponse])
async def list_memories(
    user_id: int = Query(None),
    session_id: int = Query(None),
    pipeline_version: Optional[str] = Query(None, description="Filter by pipeline version: v1 or v2"),
    db: Session = Depends(get_db)
):
    """List memories with optional filters"""
    query = db.query(Memory)
    if user_id:
        query = query.filter(Memory.user_id == user_id)
    if session_id:
        query = query.filter(Memory.session_id == session_id)
    if pipeline_version:
        query = query.filter(Memory.pipeline_version == pipeline_version)
    
    memories = query.order_by(Memory.created_at.desc()).all()
    return memories


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: int, db: Session = Depends(get_db)):
    """Get memory by ID"""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory
