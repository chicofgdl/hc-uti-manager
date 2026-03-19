from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from providers.interfaces.paciente_provider_interface import PacienteProviderInterface


class PacienteAppSqliteProvider(PacienteProviderInterface):
    """Paciente provider backed by the app database, never by CSV."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar_pacientes(self) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text(
                """
                SELECT
                    external_id AS codigo,
                    COALESCE(name, '') AS nome,
                    NULL AS dt_nascimento,
                    location
                FROM patients
                WHERE external_id IS NOT NULL
                ORDER BY external_id
                """
            )
        )
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def obter_paciente_por_codigo(self, codigo: int) -> Dict[str, Any]:
        result = await self.session.execute(
            text(
                """
                SELECT
                    external_id AS codigo,
                    COALESCE(name, '') AS nome,
                    NULL AS dt_nascimento,
                    NULL AS sexo,
                    NULL AS cor,
                    NULL AS nome_mae,
                    NULL AS nome_pai,
                    location
                FROM patients
                WHERE external_id = :codigo
                LIMIT 1
                """
            ),
            {"codigo": str(codigo)},
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente não encontrado",
            )
        return dict(row)
