import os
from typing import Callable
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from providers.interfaces.paciente_provider_interface import PacienteProviderInterface
from providers.implementations.paciente_postgres_provider import PacientePostgresProvider
from providers.implementations.paciente_csv_provider import PacienteCsvProvider
from resources.database import get_aghu_db_session

# 1. Funções "getter" simples e independentes (privadas por convenção)
def _get_paciente_postgres_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> PacienteProviderInterface:
    return PacientePostgresProvider(session=session)

def _get_paciente_csv_provider() -> PacienteProviderInterface:
    csv_path = os.getenv("PACIENTE_CSV_PATH", "data/pacientes.csv")
    return PacienteCsvProvider(csv_path=csv_path)

# 2. A FÁBRICA: A única função que o roteador vai conhecer.
def get_paciente_provider(strategy: str) -> Callable[..., PacienteProviderInterface]:
    """
    Esta é uma fábrica. Baseado na string 'strategy', ela não retorna o provedor,
    mas sim a FUNÇÃO DE DEPENDÊNCIA correta que o FastAPI deve usar.
    """
    if strategy.upper() == "POSTGRES":
        return _get_paciente_postgres_provider
    elif strategy.upper() == "CSV":
        return _get_paciente_csv_provider
    else:
        raise ValueError(f"Estratégia de provedor desconhecida: {strategy}")

# --- Leitos: provider + controller wiring ---------------------------------
from controllers.leitos_controller import LeitosController
from providers.interfaces.leito_provider_interface import LeitoProviderInterface
from providers.implementations.banco.leito_postegres_provide import LeitoBancoBProvider
from providers.implementations.banco_aghu.leito_csv_provider import LeitoCsvProvider

async def _get_leito_banco_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> LeitoProviderInterface:
    return LeitoBancoBProvider(session=session)

def _get_leito_csv_provider() -> LeitoProviderInterface:
    leitos_csv = os.getenv("LEITOS_CSV_PATH", "data/leitos.csv")
    pacientes_csv = os.getenv("PACIENTE_CSV_PATH", "data/pacientes.csv")
    # Informational: ensure files exist — helps debug issues during startup or requests
    if not os.path.isfile(leitos_csv):
        print(f"WARNING: leitos CSV not found at {leitos_csv}")
    if not os.path.isfile(pacientes_csv):
        print(f"WARNING: pacientes CSV not found at {pacientes_csv}")
    try:
        return LeitoCsvProvider(leitos_csv=leitos_csv, pacientes_csv=pacientes_csv)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("ERROR constructing LeitoCsvProvider:\n", tb)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail={"error": str(e), "trace": tb})

def get_leito_provider() -> Callable[..., LeitoProviderInterface]:
    """Return dependency function for leito provider based on env vars."""
    selected = "banco" if os.getenv("POSTGRES_DSN") else "csv"
    print(f"INFO: Selected leito provider strategy: {selected}")
    if os.getenv("POSTGRES_DSN"):
        return _get_leito_banco_provider
    return _get_leito_csv_provider

def get_leito_controller(
    provider: LeitoProviderInterface = Depends(get_leito_provider())
) -> LeitosController:
    """Dependency that returns a LeitosController wired with a leito provider.
    Wrap construction in error handling to provide clear server logs on failure."""
    try:
        return LeitosController(provider)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("ERROR constructing LeitosController:\n", tb)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail={"error": str(e), "trace": tb})
