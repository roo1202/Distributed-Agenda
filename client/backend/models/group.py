from sqlalchemy import Column, Integer, Boolean, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy.orm import relationship
from .group_user_association import association_table

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    hierarchy = Column(Boolean)
    creator = Column(BigInteger, nullable=False)
    users = relationship("User", secondary=association_table, back_populates="groups")


