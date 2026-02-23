"""add users table

Revision ID: c3d4e5f6g7
Revises: b2c3d4e5f6
Create Date: 2026-02-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        hashed_password VARCHAR(128) NOT NULL,
        role VARCHAR(50) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS users;")