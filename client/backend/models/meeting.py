from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    state = Column(String)
    
    event = relationship("Event", back_populates="meetings")
    user = relationship("User", back_populates="meetings")
