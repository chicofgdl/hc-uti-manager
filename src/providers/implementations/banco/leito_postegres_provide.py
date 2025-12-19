from sqlalchemy.sql import text
from fastapi import HTTPException, status
from helpers.datetime_helper import utcnow
from typing import List, Dict, Any

class LeitoBancoBProvider:
    def __init__(self, session):
        self.session = session

    async def upsert(self, leito: dict):
        query = text("""
            INSERT INTO leitos (
                lto_lto_id, status, tipo, alta_solicitada,
                prontuario_atual, idade_atual, especialidade_atual,
                prontuario_proximo, idade_proximo, especialidade_proximo,
                atualizado_em
            )
            VALUES (
                :lto_lto_id, :status, :tipo, :alta_solicitada,
                :prontuario_atual, :idade_atual, :especialidade_atual,
                :prontuario_proximo, :idade_proximo, :especialidade_proximo,
                :atualizado_em
            )
            ON CONFLICT (lto_lto_id)
            DO UPDATE SET
                status = EXCLUDED.status,
                tipo = EXCLUDED.tipo,
                alta_solicitada = EXCLUDED.alta_solicitada,
                prontuario_atual = EXCLUDED.prontuario_atual,
                idade_atual = EXCLUDED.idade_atual,
                especialidade_atual = EXCLUDED.especialidade_atual,
                prontuario_proximo = EXCLUDED.prontuario_proximo,
                idade_proximo = EXCLUDED.idade_proximo,
                especialidade_proximo = EXCLUDED.especialidade_proximo,
                atualizado_em = EXCLUDED.atualizado_em
        """)

        await self.session.execute(query, leito)
        await self.session.commit()

    async def listar_leitos(self):
        result = await self.session.execute(text("SELECT * FROM leitos"))
        return result.mappings().all()
    
    async def reservar_leito(
        self,
        lto_lto_id: str,
        prontuario: int,
        idade: int,
        especialidade: str
    ):

        result = await self.session.execute(
            text("""
            SELECT alta_solicitada
            FROM leitos
            WHERE lto_lto_id = :lto_lto_id
            FOR UPDATE
            """),
            {"lto_lto_id": lto_lto_id}
        )

        leito = result.fetchone()

        if not leito:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leito não encontrado"
            )

        if not leito.alta_solicitada:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Leito não possui alta solicitada"
            )

        await self.session.execute(
            text("""
            UPDATE leitos
            SET
                prontuario_proximo = :prontuario,
                idade_proximo = :idade,
                especialidade_proximo = :especialidade,
                atualizado_em = :atualizado_em
            WHERE lto_lto_id = :lto_lto_id
            """),
            {
                "lto_lto_id": lto_lto_id,
                "prontuario": prontuario,
                "idade": idade,
                "especialidade": especialidade,
                "atualizado_em": utcnow()
            }
        )

        await self.session.commit()

    async def solicitar_alta(self, lto_lto_id: str) -> None:
        print("Solicitando alta para leito:", lto_lto_id)

        # Check current value and existence
        select_q = text("""
            SELECT alta_solicitada
            FROM leitos
            WHERE lto_lto_id = :lto_lto_id
            FOR UPDATE
        """)
        result = await self.session.execute(select_q, {"lto_lto_id": lto_lto_id})
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leito não encontrado")

        print("Current alta_solicitada:", getattr(row, 'alta_solicitada', None))

        # Perform update
        update_q = text("""
            UPDATE leitos
            SET
                alta_solicitada = true,
                atualizado_em = NOW()
            WHERE lto_lto_id = :lto_lto_id
            RETURNING alta_solicitada
        """)
        update_res = await self.session.execute(update_q, {"lto_lto_id": lto_lto_id})
        await self.session.commit()

        updated = update_res.fetchone()
        print("Update returned:", updated)

        # Verify
        verify = await self.session.execute(
            text("SELECT alta_solicitada FROM leitos WHERE lto_lto_id = :lto_lto_id"),
            {"lto_lto_id": lto_lto_id}
        )
        verify_row = verify.fetchone()
        print("Post-update alta_solicitada:", getattr(verify_row, 'alta_solicitada', None))

        if not verify_row or not getattr(verify_row, 'alta_solicitada', False):
            raise HTTPException(status_code=500, detail="Failed to set alta_solicitada=true")

    async def cancelar_alta(self, lto_lto_id: str) -> None:
        query = text("""
            UPDATE leitos
            SET
                alta_solicitada = false,
                prontuario_proximo = NULL,
                idade_proximo = NULL,
                especialidade_proximo = NULL,
                atualizado_em = NOW()
            WHERE lto_lto_id = :lto_lto_id
        """)
        await self.session.execute(query, {"lto_lto_id": lto_lto_id})
        await self.session.commit()

    async def listar_leitos_disponiveis_para_reserva(self):
        query = text("""
                SELECT
                    lto_lto_id,
                    status,
                    tipo,
                    alta_solicitada,
                    prontuario_atual,
                    idade_atual,
                    especialidade_atual,
                    prontuario_proximo,
                    idade_proximo,
                    especialidade_proximo,
                    atualizado_em
                FROM leitos
                WHERE
                    alta_solicitada = true
                    AND prontuario_proximo IS NULL
                ORDER BY atualizado_em DESC
        """)

        result = await self.session.execute(query)
        return result.mappings().all()
    
    async def listar_leitos(self) -> List[Dict[str, Any]]:
        query = text("""
            SELECT
                lto_lto_id,
                status,
                tipo,
                alta_solicitada,
                prontuario_atual,
                idade_atual,
                especialidade_atual,
                prontuario_proximo,
                idade_proximo,
                especialidade_proximo,
                atualizado_em
            FROM leitos
            ORDER BY lto_lto_id
        """)

        result = await self.session.execute(query)
        return [dict(row) for row in result.mappings().all()]