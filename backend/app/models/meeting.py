from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    state = Column(String)
    
    event = relationship("Event", back_populates="meetings")
    user = relationship("User", back_populates="meetings")
