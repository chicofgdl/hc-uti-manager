"""add solicitacoes and cancelamentos tables

Revision ID: a1b2c3d4e5f6
Revises: 8a2efbe37bb6
Create Date: 2026-02-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '8a2efbe37bb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create solicitacoes_reserva
    op.execute("""
    CREATE TABLE IF NOT EXISTS solicitacoes_reserva (
        id SERIAL PRIMARY KEY,
        prontuario_paciente VARCHAR(20) NOT NULL,
        idade_paciente INTEGER NOT NULL,
        especialidade_paciente VARCHAR(100) NOT NULL,
        status VARCHAR(20) NOT NULL
            CHECK (status IN ('PENDENTE', 'APROVADA', 'NEGADA', 'CANCELADA')),
        lto_lto_id VARCHAR(10),
        motivo_negacao TEXT,
        criada_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        atualizada_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_solicitacao_reserva_leito
            FOREIGN KEY (lto_lto_id)
            REFERENCES leitos (lto_lto_id)
            ON UPDATE CASCADE
            ON DELETE SET NULL
    );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_reserva_status ON solicitacoes_reserva(status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_reserva_criada_em ON solicitacoes_reserva(criada_em DESC);")

    # cancelamentos_reserva
    op.execute("""
    CREATE TABLE IF NOT EXISTS cancelamentos_reserva (
        id SERIAL PRIMARY KEY,
        solicitacao_reserva_id INTEGER NOT NULL,
        cancelado_por VARCHAR(100) NOT NULL,
        motivo TEXT,
        cancelado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_cancelamento_reserva
            FOREIGN KEY (solicitacao_reserva_id)
            REFERENCES solicitacoes_reserva (id)
            ON DELETE CASCADE
    );
    """)

    # solicitacoes_transferencia
    op.execute("""
    CREATE TABLE IF NOT EXISTS solicitacoes_transferencia (
        id SERIAL PRIMARY KEY,
        prontuario_paciente VARCHAR(20) NOT NULL,
        idade_paciente INTEGER NOT NULL,
        especialidade_paciente VARCHAR(100) NOT NULL,
        status VARCHAR(20) NOT NULL
            CHECK (status IN ('PENDENTE', 'ACEITA', 'NEGADA', 'CANCELADA')),
        lto_lto_id VARCHAR(10),
        criada_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        atualizada_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_transferencia_leito
            FOREIGN KEY (lto_lto_id)
            REFERENCES leitos (lto_lto_id)
            ON UPDATE CASCADE
            ON DELETE SET NULL
    );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_transferencia_status ON solicitacoes_transferencia(status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_transferencia_criada_em ON solicitacoes_transferencia(criada_em DESC);")

    # cancelamentos_transferencia
    op.execute("""
    CREATE TABLE IF NOT EXISTS cancelamentos_transferencia (
        id SERIAL PRIMARY KEY,
        solicitacao_transferencia_id INTEGER NOT NULL,
        cancelado_por VARCHAR(100) NOT NULL,
        motivo TEXT,
        cancelado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        CONSTRAINT fk_cancelamento_transferencia
            FOREIGN KEY (solicitacao_transferencia_id)
            REFERENCES solicitacoes_transferencia (id)
            ON DELETE CASCADE
    );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cancelamentos_transferencia CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_transferencia_criada_em;")
    op.execute("DROP INDEX IF EXISTS idx_transferencia_status;")
    op.execute("DROP TABLE IF EXISTS solicitacoes_transferencia CASCADE;")

    op.execute("DROP TABLE IF EXISTS cancelamentos_reserva CASCADE;")
    op.execute("DROP INDEX IF EXISTS idx_reserva_criada_em;")
    op.execute("DROP INDEX IF EXISTS idx_reserva_status;")
    op.execute("DROP TABLE IF EXISTS solicitacoes_reserva CASCADE;")
