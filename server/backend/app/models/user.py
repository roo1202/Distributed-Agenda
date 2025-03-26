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


    def __json__(self, basic=True):
        if basic:
            return {
                'id': self.id,
                "name": self.name,
                "email": self.email,
                "hashed_password": self.hashed_password
            }
        return {
            'id': self.id,
            "name": self.name,
            "email": self.email,
            "hashed_password": self.hashed_password,
            'groups': [group.__json__() for group in self.groups] if self.groups else [],
            'meetings': [meeting.__json__() for meeting in self.meetings] if self.meetings else [],
            'notifications': [notification.__json__() for notification in self.notifications] if self.notifications else []
        }