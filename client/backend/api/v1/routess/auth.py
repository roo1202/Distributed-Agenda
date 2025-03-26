from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from client import Client
from schemas.auth import Token
from schemas.user import UserBase, UserCreate
from auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from datetime import timedelta
from passlib.context import CryptContext

router = APIRouter()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


@router.post("/register", response_model=UserBase)
def register(user: UserCreate, request: Request):
    client:Client = request.app.state.client  
    db_user = client.get_user_by_email(user_email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        client.create_account(user_name=user.name, user_email=user.email, password=user.password)
        return UserBase(email=user.email)

@router.post("/token", response_model=Token)
def login_for_access_token(request: Request , form_data: OAuth2PasswordRequestForm = Depends()):
    client:Client = request.app.state.client  
    user = client.get_user_by_email(user_email=form_data.username)
    print(user)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user['email']}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "user_name": user['name']}
