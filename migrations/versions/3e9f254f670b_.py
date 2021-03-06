"""empty message

Revision ID: 3e9f254f670b
Revises: 5d0689d364f
Create Date: 2014-06-27 18:57:04.505541

"""

# revision identifiers, used by Alembic.
revision = '3e9f254f670b'
down_revision = '5d0689d364f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('alliance', sa.Column('name', sa.String(length=64), nullable=True))
    op.add_column('corporation', sa.Column('name', sa.String(length=64), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('corporation', 'name')
    op.drop_column('alliance', 'name')
    ### end Alembic commands ###
