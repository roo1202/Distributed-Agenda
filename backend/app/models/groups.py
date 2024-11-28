from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Groups(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    members_count = Column(Integer)
    