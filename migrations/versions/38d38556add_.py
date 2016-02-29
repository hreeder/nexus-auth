"""empty message

Revision ID: 38d38556add
Revises: 5ae19da00343
Create Date: 2014-06-23 22:33:01.977977

"""

# revision identifiers, used by Alembic.
revision = '38d38556add'
down_revision = '5ae19da00343'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('api_key', sa.Column('accessMask', sa.Integer(), nullable=True))
    op.add_column('api_key', sa.Column('expiry', sa.DateTime(), nullable=True))
    op.add_column('api_key', sa.Column('status', sa.SmallInteger(), nullable=True))
    op.add_column('api_key', sa.Column('type', sa.SmallInteger(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('api_key', 'type')
    op.drop_column('api_key', 'status')
    op.drop_column('api_key', 'expiry')
    op.drop_column('api_key', 'accessMask')
    ### end Alembic commands ###
