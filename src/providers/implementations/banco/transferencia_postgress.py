from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from typing import List, Optional


class TransferenciaPostgresProvider:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(self, data):
        await self.session.execute(text("""
            INSERT INTO transferencias_paciente
            (prontuario_paciente, idade_paciente, especialidade_paciente)
            VALUES (:p, :i, :e)
        """), {
            "p": data["prontuario_paciente"],
            "i": data["idade_paciente"],
            "e": data["especialidade_paciente"]
        })
        await self.session.commit()

    async def listar(self):
        result = await self.session.execute(text("""
            SELECT *
            FROM transferencias_paciente
            ORDER BY solicitada_em DESC
        """))
        return result.mappings().all()

    async def aceitar(self, transferencia_id: int, leito_id: str):
        async with self.session.begin():
            # 1️⃣ Atualiza transferência
            await self.session.execute(text("""
                UPDATE transferencias_paciente
                SET
                    status = 'APROVADA',
                    leito_id = :leito,
                    atualizada_em = NOW()
                WHERE id = :id
            """), {
                "id": transferencia_id,
                "leito": leito_id
            })

            # 2️⃣ Busca dados do paciente
            result = await self.session.execute(text("""
                SELECT prontuario_paciente, idade_paciente, especialidade_paciente
                FROM transferencias_paciente
                WHERE id = :id
            """), {"id": transferencia_id})

            paciente = result.fetchone()

            # 3️⃣ Ocupa o leito
            await self.session.execute(text("""
                UPDATE leitos
                SET
                    status = 'OCUPADO',
                    prontuario_atual = :p,
                    idade_atual = :i,
                    especialidade_atual = :e,
                    atualizado_em = NOW()
                WHERE lto_lto_id = :leito
            """), {
                "p": getattr(paciente, 'prontuario_paciente', None),
                "i": getattr(paciente, 'idade_paciente', None),
                "e": getattr(paciente, 'especialidade_paciente', None),
                "leito": leito_id
            })

    async def negar(self, transferencia_id: int, motivo: str | None):
        await self.session.execute(text("""
            UPDATE transferencias_paciente
            SET
                status = 'NEGADA',
                motivo_negacao = :motivo,
                atualizada_em = NOW()
            WHERE id = :id
        """), {
            "id": transferencia_id,
            "motivo": motivo
        })
        await self.session.commit()
