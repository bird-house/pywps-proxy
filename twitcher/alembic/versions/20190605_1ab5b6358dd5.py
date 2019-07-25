"""dev

Revision ID: 1ab5b6358dd5
Revises: d39766e64a84
Create Date: 2019-06-05 16:25:36.793494

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ab5b6358dd5'
down_revision = 'd39766e64a84'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('client',
    sa.Column('client_id', sa.String(length=40), nullable=False),
    sa.Column('client_secret', sa.String(length=55), nullable=False),
    sa.PrimaryKeyConstraint('client_id', name=op.f('pk_client'))
    )
    op.create_index(op.f('ix_client_client_secret'), 'client', ['client_secret'], unique=True)
    op.create_table('token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.String(length=40), nullable=False),
    sa.Column('token_type', sa.String(length=40), nullable=True),
    sa.Column('access_token', sa.String(length=255), nullable=True),
    sa.Column('refresh_token', sa.String(length=255), nullable=True),
    sa.Column('expires', sa.DateTime(), nullable=True),
    sa.Column('scope', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['client.client_id'], name=op.f('fk_token_client_id_client'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_token'))
    )
    op.drop_index('token_index', table_name='access_tokens')
    op.drop_table('access_tokens')
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('access_tokens',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('token', sa.TEXT(), nullable=True),
    sa.Column('expires_at', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint('id', name='pk_access_tokens')
    )
    op.create_index('token_index', 'access_tokens', ['token'], unique=1)
    op.drop_table('token')
    op.drop_index(op.f('ix_client_client_secret'), table_name='client')
    op.drop_table('client')
    # ### end Alembic commands ###
