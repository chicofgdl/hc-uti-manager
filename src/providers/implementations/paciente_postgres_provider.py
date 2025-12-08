import os
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..interfaces.paciente_provider_interface import PacienteProviderInterface

def get_sql_query(file_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Ajuste no caminho para voltar dois níveis (implementations -> providers -> src) e depois entrar em providers/sql
    sql_file_path = os.path.join(base_dir, '..', 'sql', file_path)
    try:
        with open(sql_file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(f"Arquivo SQL não encontrado em: {sql_file_path}")

class PacientePostgresProvider(PacienteProviderInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar_pacientes(self) -> List[Dict[str, Any]]:
        query = text(
          """
          SELECT
                id,
                leito_numero,
                desativado,
                em_higienizacao,
                alta_solicitada,
                status_interno,
                observacoes,
                usuario_responsavel,
                atualizado_em
            FROM uti.leito_interno
            ORDER BY leito_numero
          """
        )
        
        result = await self.session.execute(query)
        pacientes = result.mappings().all()
        return [dict(paciente) for paciente in pacientes]

    async def obter_paciente_por_codigo(self, codigo: int) -> Dict[str, Any]:
        query = text("""
            SELECT
                id,
                leito_numero,
                desativado,
                em_higienizacao,
                alta_solicitada,
                status_interno,
                observacoes,
                usuario_responsavel,
                atualizado_em
            FROM uti.leito_interno
            WHERE id = :codigo
        """)

        result = await self.session.execute(query, {"codigo": codigo})
        row = result.mappings().first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro não encontrado na tabela uti.leito_interno.",
            )

        return dict(row)
