"""add groups to refresh token

Revision ID: 8a2efbe37bb6
Revises: df72b10ec0f3
Create Date: 2025-11-05 18:13:21.216513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a2efbe37bb6'
down_revision: Union[str, Sequence[str], None] = 'df72b10ec0f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make drops idempotent to avoid failing when indexes/tables are already absent
    try:
        op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_id")
        op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_token")
        op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_user_id")
        op.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE")
    except Exception:
        # If DB doesn't support IF EXISTS, fallback to safe alembic operations
        try:
            op.drop_index(op.f('ix_refresh_tokens_id'), table_name='refresh_tokens')
        except Exception:
            pass
        try:
            op.drop_index(op.f('ix_refresh_tokens_token'), table_name='refresh_tokens')
        except Exception:
            pass
        try:
            op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
        except Exception:
            pass
        try:
            op.drop_table('refresh_tokens')
        except Exception:
            pass


def downgrade() -> None:
    pass
