from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Person, Memory, MemoryPerson
from app.schemas import PersonResponse, MemoryResponse

router = APIRouter()


class MergeRequest(BaseModel):
    target_person_id: int


@router.get("/", response_model=list[PersonResponse])
async def list_persons(
    user_id: int,
    pipeline_version: Optional[str] = Query(None, description="Filter by pipeline version: v1 or v2"),
    db: Session = Depends(get_db)
):
    """List all persons for a user, optionally filtered by pipeline_version"""
    query = db.query(Person).filter(Person.user_id == user_id)
    if pipeline_version:
        query = query.filter(Person.pipeline_version == pipeline_version)
    persons = query.all()
    return persons


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(person_id: int, db: Session = Depends(get_db)):
    """Get person by ID"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.get("/{person_id}/memories", response_model=list[MemoryResponse])
async def get_person_memories(person_id: int, db: Session = Depends(get_db)):
    """Get all memories linked to a person"""
    memory_ids = db.query(MemoryPerson.memory_id).filter(
        MemoryPerson.person_id == person_id
    ).all()
    memory_ids = [m[0] for m in memory_ids]
    
    memories = db.query(Memory).filter(Memory.id.in_(memory_ids)).all()
    return memories


@router.post("/{person_id}/merge")
async def merge_persons(
    person_id: int,
    request: MergeRequest,
    db: Session = Depends(get_db)
):
    """Merge two persons into one"""
    person = db.query(Person).filter(Person.id == person_id).first()
    target = db.query(Person).filter(Person.id == request.target_person_id).first()
    
    if not person or not target:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Move all memory links to target (handle duplicates)
    source_links = db.query(MemoryPerson).filter(
        MemoryPerson.person_id == person_id
    ).all()
    
    for link in source_links:
        # Check if target already has this memory
        existing = db.query(MemoryPerson).filter(
            MemoryPerson.memory_id == link.memory_id,
            MemoryPerson.person_id == request.target_person_id
        ).first()
        
        if not existing:
            link.person_id = request.target_person_id
        else:
            db.delete(link)
    
    # Update first_seen_memory_id if needed
    if person.first_seen_memory_id and not target.first_seen_memory_id:
        target.first_seen_memory_id = person.first_seen_memory_id
    
    # Delete source person
    db.delete(person)
    db.commit()
    
    return {"message": f"Person {person_id} merged into {request.target_person_id}"}
