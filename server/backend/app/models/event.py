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


    def __json__(self):
        return {
            'id': self.id,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'state': self.state,
            'visibility': self.visibility,
            'user_id': self.user_id,
            #'meetings': [meeting.__json__() for meeting in self.meetings] if self.meetings else []
        }