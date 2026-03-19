from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text


class TransferenciaPostgresProvider:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(self, data):
        await self.session.execute(
            text(
                """
                INSERT INTO solicitacoes_transferencia
                    (prontuario_paciente, idade_paciente, especialidade_paciente, status, lto_lto_id, criada_em, atualizada_em)
                VALUES
                    (:p, :i, :e, 'PENDENTE', NULL, NOW(), NOW())
                """
            ),
            {
                "p": str(data["prontuario_paciente"]),
                "i": int(data["idade_paciente"]),
                "e": data["especialidade_paciente"],
            },
        )
        await self.session.commit()

    async def listar(self):
        result = await self.session.execute(
            text(
                """
                SELECT *
                FROM solicitacoes_transferencia
                ORDER BY criada_em DESC
                """
            )
        )
        return result.mappings().all()

    async def aceitar(self, transferencia_id: int, leito_id: str):
        async with self.session.begin():
            await self.session.execute(
                text(
                    """
                    UPDATE solicitacoes_transferencia
                    SET
                        status = 'ACEITA',
                        lto_lto_id = :leito,
                        atualizada_em = NOW()
                    WHERE id = :id
                    """
                ),
                {
                    "id": transferencia_id,
                    "leito": leito_id,
                },
            )

            result = await self.session.execute(
                text(
                    """
                    SELECT prontuario_paciente, idade_paciente, especialidade_paciente
                    FROM solicitacoes_transferencia
                    WHERE id = :id
                    """
                ),
                {"id": transferencia_id},
            )

            paciente = result.fetchone()

            await self.session.execute(
                text(
                    """
                    UPDATE leitos
                    SET
                        status = 'OCUPADO',
                        alta_solicitada = FALSE,
                        prontuario_atual = :p,
                        idade_atual = :i,
                        especialidade_atual = :e,
                        prontuario_proximo = NULL,
                        idade_proximo = NULL,
                        especialidade_proximo = NULL,
                        atualizado_em = NOW()
                    WHERE lto_lto_id = :leito
                    """
                ),
                {
                    "p": int(getattr(paciente, "prontuario_paciente", 0) or 0),
                    "i": getattr(paciente, "idade_paciente", None),
                    "e": getattr(paciente, "especialidade_paciente", None),
                    "leito": leito_id,
                },
            )

    async def negar(self, transferencia_id: int, motivo: str | None):
        await self.session.execute(
            text(
                """
                UPDATE solicitacoes_transferencia
                SET
                    status = 'NEGADA',
                    atualizada_em = NOW()
                WHERE id = :id
                """
            ),
            {
                "id": transferencia_id,
            },
        )
        await self.session.commit()
