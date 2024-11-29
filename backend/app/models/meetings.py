from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    state = Column(String)

