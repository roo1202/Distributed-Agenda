from app.db.base import Base
from sqlalchemy import Column, Interval, Integer, String
from datetime import timedelta

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    duration = Column(Interval)
    description = Column(String)
    state = Column(String)

