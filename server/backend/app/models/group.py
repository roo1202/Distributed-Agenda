from sqlalchemy import Column, Integer, Boolean, String, BigInteger
from db.base import Base
from sqlalchemy.orm import relationship
from .group_user_association import association_table

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    hierarchy = Column(Boolean)
    creator = Column(BigInteger, nullable=False)
    users = relationship("User", secondary=association_table, back_populates="groups")


    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
            'hierarchy': self.hierarchy,
            'creator': self.creator,
            # 'users': [user.__json__(basic=True) for user in self.users] if self.users else []
        }
