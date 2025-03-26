from sqlalchemy import UniqueConstraint
from sqlalchemy import Column, Integer, String, ForeignKey, DATETIME, BigInteger
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    text = Column(String, nullable=False)
    time = Column(DATETIME, nullable=False)
    
    __table_args__ = (UniqueConstraint('user_id', 'id'),)
