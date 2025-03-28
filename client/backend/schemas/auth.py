# schemas/auth.py
from pydantic import BaseModel

class Token(BaseModel):
    user_name : str
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

    class Config:
        from_attributes  = True