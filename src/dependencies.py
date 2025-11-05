import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .providers.interfaces.paciente_provider_interface import PacienteProviderInterface
from .providers.implementations.paciente_postgres_provider import PacientePostgresProvider
from .providers.implementations.paciente_csv_provider import PacienteCsvProvider
from .resources.database import get_aghu_db_session

# Mapeia o tipo de provedor para a sua classe correspondente
PROVIDER_MAP = {
    "POSTGRES": PacientePostgresProvider,
    "CSV": PacienteCsvProvider,
}

def get_paciente_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> PacienteProviderInterface:
    """
    Decide qual implementação do provedor de pacientes usar com base na variável de ambiente.
    """
    provider_type = os.getenv("PACIENTE_PROVIDER_TYPE", "POSTGRES").upper()
    ProviderClass = PROVIDER_MAP.get(provider_type)

    if not ProviderClass:
        raise ValueError(f"Tipo de provedor inválido: {provider_type}. Válidos são: {list(PROVIDER_MAP.keys())}")

    # Se a classe for a do Postgres, ela precisa da sessão do banco de dados.
    if ProviderClass == PacientePostgresProvider:
        return PacientePostgresProvider(session=session)
    else:
        # Outros provedores (como o CSV) são instanciados sem argumentos.
        return ProviderClass()
