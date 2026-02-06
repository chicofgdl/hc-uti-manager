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
    # Tabela já passa a conter coluna groups na migration anterior. Nada a fazer.
    pass


def downgrade() -> None:
    pass
