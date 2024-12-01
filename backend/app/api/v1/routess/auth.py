# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.auth import Token
from app.schemas.user import UserBase, UserCreate
from app.services.user_service import create_user, get_user_by_email, verify_password
from app.auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user
from app.api.v1.routes import get_db
from datetime import timedelta

from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserBase)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user_email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db, name=user.name, email=user.email, password=user.password)

@router.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(db, user_email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserBase)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user