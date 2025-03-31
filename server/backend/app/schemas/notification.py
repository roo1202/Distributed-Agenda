from pydantic import BaseModel
from datetime import datetime

class NotifResponse(BaseModel):
    time : datetime
    text : str

    class Config:
        from_attributes  = True