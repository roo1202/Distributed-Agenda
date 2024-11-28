from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base
from datetime import datetime

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    state = Column(String)
    user_id = Column(Integer, index=True)

