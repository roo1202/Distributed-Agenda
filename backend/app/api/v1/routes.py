from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.user_service import create_user
from app.schemas.user import UserCreate, UserResponse
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