"""Initial migration

Revision ID: 954c820d7e2d
Revises: 
Create Date: 2025-04-08 02:16:22.730254

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '954c820d7e2d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('game_stats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('replay_file', sa.String(length=500), nullable=False),
    sa.Column('replay_hash', sa.String(length=64), nullable=False),
    sa.Column('game_version', sa.String(length=50), nullable=True),
    sa.Column('map', sa.String(length=100), nullable=True),
    sa.Column('game_type', sa.String(length=50), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('winner', sa.String(length=100), nullable=True),
    sa.Column('players', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('event_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('key_events', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('played_on', sa.DateTime(), nullable=True),
    sa.Column('parse_iteration', sa.Integer(), nullable=True),
    sa.Column('is_final', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('replay_hash', 'is_final', name='uq_replay_final')
    )
    with op.batch_alter_table('game_stats', schema=None) as batch_op:
        batch_op.create_index('ix_replay_hash_iteration', ['replay_hash', 'parse_iteration'], unique=False)
        batch_op.create_index('ix_replay_iteration', ['replay_file', 'parse_iteration'], unique=False)

    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uid', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('in_game_name', sa.String(), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=True),
    sa.Column('wallet_address', sa.String(length=100), nullable=True),
    sa.Column('lock_name', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('uid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    with op.batch_alter_table('game_stats', schema=None) as batch_op:
        batch_op.drop_index('ix_replay_iteration')
        batch_op.drop_index('ix_replay_hash_iteration')

    op.drop_table('game_stats')
    # ### end Alembic commands ###
