from pydantic import BaseModel
from datetime import datetime

class EventPrivate(BaseModel):
    start_time:datetime
    end_time:datetime
    visibility:str

class EventBase(EventPrivate):
    description: str

class EventCreate(EventBase):
    state : str

class EventResponse(EventCreate):
    id: int
    

    class Config:
        from_attributes  = True