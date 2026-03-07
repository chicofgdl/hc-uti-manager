from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from typing import List, Dict, Any


class NotificacaoProvider:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(
        self,
        tipo: str,
        mensagem: str,
        role_destino: str
    ) -> None:
        query = text("""
            INSERT INTO notificacoes (
                tipo,
                mensagem,
                role_destino,
                lida,
                criada_em
            )
            VALUES (
                :tipo,
                :mensagem,
                :role_destino,
                FALSE,
                NOW()
            )
        """)

        await self.session.execute(query, {
            "tipo": tipo,
            "mensagem": mensagem,
            "role_destino": role_destino
        })
        await self.session.commit()

    async def listar_por_role(self, role: str) -> List[Dict[str, Any]]:
        query = text("""
            SELECT
                id,
                tipo,
                mensagem,
                role_destino,
                lida,
                criada_em
            FROM notificacoes
            WHERE role_destino = :role
            ORDER BY criada_em DESC
        """)

        result = await self.session.execute(query, {"role": role})
        return [dict(row) for row in result.mappings().all()]

    async def marcar_como_lida(self, notificacao_id: int) -> None:
        query = text("""
            UPDATE notificacoes
            SET lida = TRUE
            WHERE id = :id
        """)

        await self.session.execute(query, {"id": notificacao_id})
        await self.session.commit()