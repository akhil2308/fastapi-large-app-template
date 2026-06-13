"""add_todo_pagination_index

Revision ID: a1b2c3d4e5f6
Revises: e758cbdc2fd0
Create Date: 2026-06-12 00:00:00.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"  # pragma: allowlist secret
down_revision: Union[str, Sequence[str], None] = "e758cbdc2fd0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Supports the ORDER BY created_at DESC, id DESC pagination query
    op.create_index(
        "ix_todos_user_active_created",
        "todos",
        ["user_id", "is_deleted", sa.text("created_at DESC"), sa.text("id DESC")],
        postgresql_where=sa.text("is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_todos_user_active_created", table_name="todos")
