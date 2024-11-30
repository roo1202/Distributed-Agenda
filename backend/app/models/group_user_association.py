from sqlalchemy import Table, Column, Integer, ForeignKey, Boolean, String
from app.db.base import Base

association_table = Table(
    'group_user_association',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)