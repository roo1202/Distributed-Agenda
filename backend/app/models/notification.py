from sqlalchemy import UniqueConstraint
from sqlalchemy import Column, Integer, String, ForeignKey, DATETIME
from app.db.base import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    text = Column(String, nullable=False)
    time = Column(DATETIME, nullable=False)
    
    __table_args__ = (UniqueConstraint('user_id', 'notification_id'),)
