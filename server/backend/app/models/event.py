from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, BigInteger
from db.base import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    state = Column(String)
    visibility = Column(String)
    user_id = Column(BigInteger, ForeignKey('users.id'))

    meetings = relationship("Meeting", back_populates="event")
