from pydantic import BaseModel
from datetime import datetime

class EventBase(BaseModel):
    id: int

class EventCreate(EventBase):
    description:str
    start_time:datetime
    end_time:datetime
    state:str

class EventResponse(EventBase):
    id: int
    description: str
    state : str
    start_time:datetime
    end_time:datetime

    class Config:
        orm_mode = True