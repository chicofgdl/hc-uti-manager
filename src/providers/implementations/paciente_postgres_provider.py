import os
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from providers.interfaces.paciente_provider_interface import PacienteProviderInterface

def get_sql_query(file_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(base_dir, '..', 'sql', 'paciente', file_path)
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(f"Arquivo SQL não encontrado em: {sql_file_path}")


class PacientePostgresProvider(PacienteProviderInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar_pacientes(self) -> List[Dict[str, Any]]:
        query_text = get_sql_query('listar_pacientes.sql')
        result = await self.session.execute(text(query_text))
        rows = result.mappings().all()
        return [dict(r) for r in rows]

    async def obter_paciente_por_codigo(self, codigo: int) -> Dict[str, Any]:
        query_text = get_sql_query('obter_paciente.sql')
        result = await self.session.execute(text(query_text), {"codigo": codigo})
        row = result.mappings().first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente não encontrado"
            )
        return dict(row)
