from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.user_service import create_user, get_users
from app.schemas.user import UserCreate, UserResponse, UserBase
from app.db.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user.name, user.email, user.password)


@router.get("/users/", response_model=List[UserBase])
def get_users_endpoint(db: Session = Depends(get_db)):
    return get_users(db)
