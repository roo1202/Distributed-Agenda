from sqlalchemy import Table, Column, Integer, ForeignKey, BigInteger
from db.base import Base

association_table = Table(
    'group_user_association',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('user_id', BigInteger, ForeignKey('users.id')),
    Column('hierarchy_level', Integer)  
)