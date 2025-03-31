from pydantic import BaseModel
from datetime import datetime

class EventPrivate(BaseModel):
    start_time:datetime
    end_time:datetime


class EventBase(EventPrivate):
    description: str
    visibility : str
    
class EventCreate(EventBase):
    state : str
    

class EventResponse(EventCreate):
    id: int
    

    class Config:
        from_attributes  = True