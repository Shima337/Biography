from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import User
from app.schemas import SessionResponse

router = APIRouter()


class UserCreate(BaseModel):
    name: str = None


class UserResponse(BaseModel):
    id: int
    name: str
    locale: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=list[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).order_by(User.created_at).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate = None,
    name: str = None,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    # Get name from body or generate default
    if user_data and user_data.name:
        user_name = user_data.name
    elif name:
        user_name = name
    else:
        # Generate default name: "User 1", "User 2", etc.
        existing_count = db.query(User).count()
        user_name = f"User {existing_count + 1}"
    
    user = User(name=user_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user (and all associated data)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted"}
