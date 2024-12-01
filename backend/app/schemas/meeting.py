from pydantic import BaseModel
from datetime import datetime

class MeetingBase(BaseModel):
    state : str

class MeetingCreate(MeetingBase):
    users_email : list[str]
    event_id : int

class MeetingResponse(MeetingBase):
    id: int

class MeetingInfo(MeetingResponse):
    user_email : str
    event_description : str
    event_id : int
    start_time : datetime
    end_time : datetime
    
class MeetingUpdate(MeetingBase):
    event_id: int

    class Config:
        from_attributes  = True