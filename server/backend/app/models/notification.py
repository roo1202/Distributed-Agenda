from sqlalchemy import UniqueConstraint
from sqlalchemy import Column, Integer, String, ForeignKey, DATETIME, BigInteger
from db.base import Base
from sqlalchemy.orm import relationship

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    text = Column(String, nullable=False)
    time = Column(DATETIME, nullable=False)
    user = relationship("User", back_populates="notifications")  
    
    __table_args__ = (UniqueConstraint('user_id', 'id'),)
