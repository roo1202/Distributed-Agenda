from pydantic import BaseModel
from datetime import datetime

class EventBase(BaseModel):
    description: str
    start_time:datetime
    end_time:datetime

class EventCreate(EventBase):
    state : str

class EventResponse(EventCreate):
    id: int
    

    class Config:
        orm_mode = True