"""empty message

Revision ID: 41a569fb745b
Revises: 390c1edf96b9
Create Date: 2014-06-26 01:18:37.144820

"""

# revision identifiers, used by Alembic.
revision = '41a569fb745b'
down_revision = '390c1edf96b9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('group', sa.Column('description', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('group', 'description')
    ### end Alembic commands ###
