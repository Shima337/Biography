from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Chapter, Memory, MemoryChapter
from app.schemas import ChapterResponse, MemoryResponse

router = APIRouter()


@router.get("/", response_model=list[ChapterResponse])
async def list_chapters(user_id: int, db: Session = Depends(get_db)):
    """List all chapters for a user"""
    chapters = db.query(Chapter).filter(
        Chapter.user_id == user_id
    ).order_by(Chapter.order_index).all()
    return chapters


@router.get("/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """Get chapter by ID"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.get("/{chapter_id}/memories", response_model=list[MemoryResponse])
async def get_chapter_memories(chapter_id: int, db: Session = Depends(get_db)):
    """Get all memories linked to a chapter"""
    memory_ids = db.query(MemoryChapter.memory_id).filter(
        MemoryChapter.chapter_id == chapter_id
    ).all()
    memory_ids = [m[0] for m in memory_ids]
    
    memories = db.query(Memory).filter(Memory.id.in_(memory_ids)).all()
    return memories


@router.get("/{chapter_id}/coverage")
async def get_chapter_coverage(chapter_id: int, db: Session = Depends(get_db)):
    """Get coverage statistics for a chapter"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    total_memories = db.query(Memory).filter(Memory.user_id == chapter.user_id).count()
    chapter_memories = db.query(MemoryChapter).filter(
        MemoryChapter.chapter_id == chapter_id
    ).count()
    
    coverage = (chapter_memories / total_memories * 100) if total_memories > 0 else 0
    
    return {
        "chapter_id": chapter_id,
        "total_memories": total_memories,
        "chapter_memories": chapter_memories,
        "coverage_percent": round(coverage, 2)
    }
