from sqlalchemy import Column, String, BigInteger
from db.base import Base
from sqlalchemy.orm import relationship
from .group_user_association import association_table

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    groups = relationship("Group", secondary=association_table, back_populates="users")
    meetings = relationship("Meeting", back_populates="user")
    notifications = relationship("Notification", back_populates="user")