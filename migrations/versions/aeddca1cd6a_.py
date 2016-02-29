"""empty message

Revision ID: aeddca1cd6a
Revises: 178ec8c0b4ef
Create Date: 2014-07-18 15:47:01.059166

"""

# revision identifiers, used by Alembic.
revision = 'aeddca1cd6a'
down_revision = '178ec8c0b4ef'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('POS', sa.Column('corp_ticker', sa.String(length=32), nullable=True))
    op.add_column('POS', sa.Column('corpid', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('POS', 'corpid')
    op.drop_column('POS', 'corp_ticker')
    ### end Alembic commands ###