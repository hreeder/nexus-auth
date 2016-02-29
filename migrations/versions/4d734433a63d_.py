"""empty message

Revision ID: 4d734433a63d
Revises: 1e5cd35569af
Create Date: 2014-06-25 14:55:18.420470

"""

# revision identifiers, used by Alembic.
revision = '4d734433a63d'
down_revision = '1e5cd35569af'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('api_key', sa.Column('lastUpdated', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('api_key', 'lastUpdated')
    ### end Alembic commands ###
