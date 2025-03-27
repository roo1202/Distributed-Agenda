from pydantic import BaseModel
from datetime import datetime

class MeetingBase(BaseModel):
    state : str
    user_id: int

class MeetingCreate(MeetingBase):
    users_email : list[str]
    event_id : int

class MeetingResponse(MeetingBase):
    id: int

class MeetingInfo(MeetingResponse):
    users_email : list[str]
    event_description : str
    event_id : int
    start_time : datetime
    end_time : datetime
    

    class Config:
        from_attributes  = True