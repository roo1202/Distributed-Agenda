from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from db.base import Base

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    state = Column(String)
    
    event = relationship("Event", back_populates="meetings")
    user = relationship("User", back_populates="meetings")


    def __json__(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'state': self.state,
            # 'event': self.event.__json__() if self.event else None,
            # 'user': self.user.__json__(basic=True) if self.user else None
        }