"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "daily_words",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), unique=True, nullable=False),
        sa.Column("word", sa.String(5), nullable=False),
        sa.Column("difficulty_rank", sa.SmallInteger(), default=5),
    )
    op.create_index("ix_daily_words_date", "daily_words", ["date"])

    op.create_table(
        "game_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("word_id", sa.Integer(), sa.ForeignKey("daily_words.id"), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("solved", sa.Boolean(), nullable=False),
        sa.Column("time_seconds", sa.Integer()),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("guess_history", sa.JSON(), nullable=False),
    )
    op.create_index("ix_game_results_user_id", "game_results", ["user_id"])
    op.create_index("ix_game_results_completed_at", "game_results", ["completed_at"])
    op.create_unique_constraint("unique_user_daily_game", "game_results", ["user_id", "word_id"])

    op.create_table(
        "user_streaks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("current_streak", sa.Integer(), default=0),
        sa.Column("longest_streak", sa.Integer(), default=0),
        sa.Column("last_played", sa.Date()),
        sa.Column("total_games", sa.Integer(), default=0),
        sa.Column("total_wins", sa.Integer(), default=0),
    )


def downgrade() -> None:
    op.drop_table("user_streaks")
    op.drop_table("game_results")
    op.drop_table("daily_words")
    op.drop_table("users")
