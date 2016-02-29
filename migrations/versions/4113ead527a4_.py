"""empty message

Revision ID: 4113ead527a4
Revises: 94ff4532762
Create Date: 2014-07-20 11:11:46.106965

"""

# revision identifiers, used by Alembic.
revision = '4113ead527a4'
down_revision = '94ff4532762'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('log_general', sa.Column('user_id', sa.Integer(), nullable=True))
    op.drop_column('log_general', 'user')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('log_general', sa.Column('user', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_column('log_general', 'user_id')
    ### end Alembic commands ###