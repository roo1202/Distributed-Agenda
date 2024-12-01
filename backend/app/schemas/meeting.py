from pydantic import BaseModel
from datetime import datetime

class MeetingBase(BaseModel):
    state : str

class MeetingCreate(MeetingBase):
    users_email : list[str]
    event_id : int

class MeetingResponse(MeetingBase):
    id: int
    
class MeetingUpdate(MeetingBase):
    event_id: int

    class Config:
        from_attributes  = True