from pydantic import BaseModel
from datetime import datetime

class MeetingBase(BaseModel):
    state : str

class MeetingCreate(MeetingBase):
    users_email : list[str]
    event_id : int

class MeetingResponse(MeetingBase):
    id: int
    event_description: str
    start_time: datetime
    end_time: datetime

class MeetingInfo(MeetingResponse):
    users_email : list[str]
    event_id : int

    class Config:
        from_attributes  = True