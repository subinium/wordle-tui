"""Add game_progress table for auto-save

Revision ID: 005
Revises: 004
Create Date: 2025-01-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_progress",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("word_id", sa.Integer(), sa.ForeignKey("daily_words.id"), nullable=False),
        sa.Column("guesses", sa.JSON(), nullable=False, default=[]),
        sa.Column("elapsed_seconds", sa.Integer(), nullable=False, default=0),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "word_id", name="unique_user_game_progress"),
    )


def downgrade() -> None:
    op.drop_table("game_progress")
