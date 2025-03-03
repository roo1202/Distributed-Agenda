from pydantic import BaseModel

class GroupBase(BaseModel):
    name: str
    hierarchy: bool

class GroupCreate(GroupBase):
    creator : int
    

class GroupUpdate(GroupBase):
    pass

class GroupResponse(GroupBase):
    id: int

    class Config:
        from_attributes  = True