"""create new tables

Revision ID: 0101089a408b
Revises: abf79d30adcc
Create Date: 2024-11-29 00:50:11.933465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0101089a408b'
down_revision: Union[str, None] = 'abf79d30adcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('meetings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('state', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meetings_event_id'), 'meetings', ['event_id'], unique=False)
    op.create_index(op.f('ix_meetings_id'), 'meetings', ['id'], unique=False)
    op.create_index(op.f('ix_meetings_user_id'), 'meetings', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_meetings_user_id'), table_name='meetings')
    op.drop_index(op.f('ix_meetings_id'), table_name='meetings')
    op.drop_index(op.f('ix_meetings_event_id'), table_name='meetings')
    op.drop_table('meetings')
    # ### end Alembic commands ###
