from pydantic import BaseModel

class GroupBase(BaseModel):
    name: str
    hierarchy: bool

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    pass

class GroupResponse(GroupBase):
    id: int

    class Config:
        orm_mode = True