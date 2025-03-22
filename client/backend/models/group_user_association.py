from sqlalchemy import Table, Column, Integer, ForeignKey, Boolean, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

association_table = Table(
    'group_user_association',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('user_id', BigInteger, ForeignKey('users.id')),
    Column('hierarchy_level', Integer)  
)