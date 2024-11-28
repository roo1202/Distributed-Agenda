from pydantic import BaseModel

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    name:str
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True