"""Saved trips

Adds the table behind "My trips". Until now the frontend kept saved trips in
localStorage under one browser-wide key, so they survived signing out and were
visible to anyone else signing in on the same browser.

Revision ID: 002
Revises: 001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'saved_trips',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        # The planner session id: how the frontend addresses a trip in its URL.
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('destination', sa.String(length=255), nullable=True),
        sa.Column('dates', sa.String(length=100), nullable=True),
        sa.Column('days', sa.Integer(), nullable=False, server_default='0'),
        # The whole itinerary payload, so the trip page rebuilds without replanning.
        sa.Column('trip', sa.JSON(), nullable=False),
        sa.Column('saved_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # Saving the same session twice updates the row rather than duplicating it.
        sa.UniqueConstraint('user_id', 'session_id', name='uq_saved_trips_user_session'),
    )
    op.create_index('ix_saved_trips_user_id', 'saved_trips', ['user_id'])
    op.create_index('ix_saved_trips_session_id', 'saved_trips', ['session_id'])
    op.create_index('ix_saved_trips_saved_at', 'saved_trips', ['saved_at'])


def downgrade() -> None:
    op.drop_index('ix_saved_trips_saved_at', table_name='saved_trips')
    op.drop_index('ix_saved_trips_session_id', table_name='saved_trips')
    op.drop_index('ix_saved_trips_user_id', table_name='saved_trips')
    op.drop_table('saved_trips')
