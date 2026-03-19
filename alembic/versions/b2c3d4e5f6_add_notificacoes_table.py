"""add notificacoes table

Revision ID: b2c3d4e5f6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS notificacoes (
        id SERIAL PRIMARY KEY,
        tipo VARCHAR(50) NOT NULL,
        mensagem TEXT NOT NULL,
        role_destino VARCHAR(50) NOT NULL,
        lida BOOLEAN NOT NULL DEFAULT FALSE,
        criada_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_notificacao_role ON notificacoes(role_destino);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_notificacao_criada_em ON notificacoes(criada_em DESC);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notificacoes;")