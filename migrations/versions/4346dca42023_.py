"""empty message

Revision ID: 4346dca42023
Revises: 41a569fb745b
Create Date: 2014-06-26 11:14:24.075725

"""

# revision identifiers, used by Alembic.
revision = '4346dca42023'
down_revision = '41a569fb745b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('group_member',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('member_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('group_admin', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['group.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'group', sa.Column('open', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'group', 'open')
    op.drop_table('group_member')
    ### end Alembic commands ###
