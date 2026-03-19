from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from typing import List, Optional


class SolicitacaoReservaProvider:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(
        self,
        prontuario: int,
        idade: int,
        especialidade: str
    ) -> int:
        query = text("""
            INSERT INTO solicitacoes_reserva (
                prontuario_paciente,
                idade_paciente,
                especialidade_paciente,
                status,
                criada_em,
                atualizada_em
            )
            VALUES (
                :prontuario,
                :idade,
                :especialidade,
                'PENDENTE',
                NOW(),
                NOW()
            )
            RETURNING id
        """)

        result = await self.session.execute(query, {
            "prontuario": prontuario,
            "idade": idade,
            "especialidade": especialidade
        })
        await self.session.commit()
        return int(result.scalar_one())

    async def listar_todas(self) -> list[dict]:
        result = await self.session.execute(text("""
            SELECT
                id,
                status,
                prontuario_paciente,
                idade_paciente,
                especialidade_paciente,
                lto_lto_id,
                criada_em,
                atualizada_em
            FROM solicitacoes_reserva
            ORDER BY criada_em DESC
        """))
        # Use AsyncResult.mappings().all() to get a list of RowMapping objects
        rows = result.mappings().all()
        return [dict(r) for r in rows]

    async def listar_pendentes(self) -> List[dict]:
        query = text("""
            SELECT
                id,
                prontuario_paciente AS prontuario,
                idade_paciente AS idade,
                especialidade_paciente AS especialidade,
                status,
                lto_lto_id,
                criada_em,
                atualizada_em
            FROM solicitacoes_reserva
            WHERE status = 'PENDENTE'
            ORDER BY criada_em
        """)

        result = await self.session.execute(query)
        return result.mappings().all()

    async def aprovar(
        self,
        solicitacao_id: int,
        lto_lto_id: str
    ) -> None:
        # Busca solicitação
        query_solicitacao = text("""
            SELECT
                prontuario_paciente,
                idade_paciente,
                especialidade_paciente
            FROM solicitacoes_reserva
            WHERE id = :id
              AND status = 'PENDENTE'
        """)

        result = await self.session.execute(
            query_solicitacao,
            {"id": solicitacao_id}
        )
        solicitacao = result.mappings().first()

        if not solicitacao:
            raise ValueError("Solicitação não encontrada ou já processada")

        # Atualiza leito (PRÓXIMO paciente)
        # Ensure target leito exists
        exists_q = text("""
            SELECT 1 FROM leitos WHERE lto_lto_id = :lto_lto_id
        """)

        exists_res = await self.session.execute(exists_q, {"lto_lto_id": lto_lto_id})
        if not exists_res.fetchone():
            raise ValueError("Leito não encontrado")

        query_leito = text("""
            UPDATE leitos
            SET
                prontuario_proximo = :prontuario,
                idade_proximo = :idade,
                especialidade_proximo = :especialidade,
                atualizado_em = NOW()
            WHERE lto_lto_id = :lto_lto_id
        """)

        # Ensure types: prontuario_proximo in `leitos` is numeric; convert if possible
        try:
            prontuario_val = int(solicitacao["prontuario_paciente"])
        except Exception:
            prontuario_val = None

        try:
            idade_val = int(solicitacao["idade_paciente"])
        except Exception:
            idade_val = None

        await self.session.execute(query_leito, {
            "lto_lto_id": lto_lto_id,
            "prontuario": prontuario_val,
            "idade": idade_val,
            "especialidade": solicitacao["especialidade_paciente"],
        })

        # Atualiza solicitação
        query_aprovar = text("""
            UPDATE solicitacoes_reserva
            SET
                status = 'APROVADA',
                lto_lto_id = :lto_lto_id,
                atualizada_em = NOW()
            WHERE id = :id
        """)

        await self.session.execute(query_aprovar, {
            "id": solicitacao_id,
            "lto_lto_id": lto_lto_id
        })

        await self.session.commit()

    async def negar(self, solicitacao_id: int, motivo: str | None = None) -> None:
        query = text("""
            UPDATE solicitacoes_reserva
            SET
                status = 'NEGADA',
                motivo_negacao = :motivo,
                atualizada_em = NOW()
            WHERE id = :id
              AND status = 'PENDENTE'
        """)

        result = await self.session.execute(query, {
            "id": solicitacao_id,
            "motivo": motivo
        })

        if result.rowcount == 0:
            raise ValueError("Solicitação não encontrada ou já processada")

        await self.session.commit()

    async def cancelar(
        self,
        solicitacao_id: int,
        perfil: str,
        motivo: str | None = None
    ) -> None:

        async with self.session.begin():

            result = await self.session.execute(text("""
                SELECT
                    id,
                    status,
                    lto_lto_id
                FROM solicitacoes_reserva
                WHERE id = :id
            """), {"id": solicitacao_id})

            solicitacao = result.mappings().first()

            if not solicitacao:
                raise ValueError("Solicitação não encontrada")

            if solicitacao.get("status") == "CANCELADA":
                return  # idempotente

            # 1️⃣ Cancela a solicitação
            await self.session.execute(text("""
                UPDATE solicitacoes_reserva
                SET
                    status = 'CANCELADA',
                    atualizada_em = NOW()
                WHERE id = :id
            """), {"id": solicitacao_id})

            # 2️⃣ Auditoria
            await self.session.execute(text("""
                INSERT INTO cancelamentos_reserva
                (solicitacao_reserva_id, cancelado_por, motivo)
                VALUES (:id, :perfil, :motivo)
            """), {
                "id": solicitacao_id,
                "perfil": perfil,
                "motivo": motivo
            })

            # 3️⃣ Libera leito SOMENTE se existir
            if solicitacao.get("lto_lto_id"):
                await self.session.execute(text("""
                    UPDATE leitos
                    SET
                        status = 'DISPONIVEL',
                        prontuario_atual = NULL,
                        idade_atual = NULL,
                        especialidade_atual = NULL,
                        prontuario_proximo = NULL,
                        idade_proximo = NULL,
                        especialidade_proximo = NULL,
                        atualizado_em = NOW()
                    WHERE lto_lto_id = :leito_id
                """), {"leito_id": solicitacao.get("lto_lto_id")})
