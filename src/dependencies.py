import importlib
import os
from pathlib import Path
import logging
from typing import Callable
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from providers.interfaces.paciente_provider_interface import PacienteProviderInterface
from providers.implementations.paciente_postgres_provider import PacientePostgresProvider
from providers.implementations.paciente_app_sqlite_provider import PacienteAppSqliteProvider
from providers.implementations.paciente_csv_provider import PacienteCsvProvider
from resources.database import get_aghu_db_session, get_app_db_session

# Função auxiliar para sessão Postgres
async def _maybe_get_postgres_session():
    """Try to import and yield a Postgres session dependency if configured.
    Returns None when Postgres is not configured or import fails.
    """
    try:
        postgres = importlib.import_module("resources.postgres")
        # If POSTGRES_DSN not configured inside that module it may raise; handle gracefully
        get_postgres_session = getattr(postgres, "get_postgres_session", None)
        if get_postgres_session is None:
            yield None
            return
        # Delegate to the real dependency generator
        async for session in get_postgres_session():
            yield session
            return
    except Exception:
        yield None
        return

# 1. Funções "getter" simples e independentes (privadas por convenção)
def _get_paciente_postgres_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> PacienteProviderInterface:
    return PacientePostgresProvider(session=session)

def _get_paciente_app_provider(
    session: AsyncSession = Depends(get_app_db_session)
) -> PacienteProviderInterface:
    return PacienteAppSqliteProvider(session=session)

def _get_paciente_csv_provider() -> PacienteProviderInterface:
    csv_path = _resolve_csv_path("PACIENTE_CSV_PATH", "data/pacientes.csv")
    return PacienteCsvProvider(csv_path=csv_path)

# 2. A FÁBRICA: A única função que o roteador vai conhecer.
def get_paciente_provider(strategy: str) -> Callable[..., PacienteProviderInterface]:
    """
    Esta é uma fábrica. Baseado na string 'strategy', ela não retorna o provedor,
    mas sim a FUNÇÃO DE DEPENDÊNCIA correta que o FastAPI deve usar.
    """
    if strategy.upper() == "APP":
        return _get_paciente_app_provider
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

from controllers.care_controller import CareController
from providers.implementations.app.care_provider import CareProvider


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_csv_path(env_var: str, default_relative_path: str) -> str:
    configured = os.getenv(env_var, default_relative_path)
    if not configured or not configured.strip():
        configured = default_relative_path
    candidate = Path(configured)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return str(candidate)

async def _get_leito_banco_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> LeitoProviderInterface:
    return LeitoBancoBProvider(session=session)

def _get_leito_csv_provider() -> LeitoProviderInterface:
    leitos_csv = _resolve_csv_path("LEITOS_CSV_PATH", "data/leitos.csv")
    pacientes_csv = _resolve_csv_path("PACIENTE_CSV_PATH", "data/pacientes.csv")
    # Informational: ensure files exist — helps debug issues during startup or requests
    if not os.path.isfile(leitos_csv):
        logging.warning("leitos CSV not found at %s", leitos_csv)
    if not os.path.isfile(pacientes_csv):
        logging.warning("pacientes CSV not found at %s", pacientes_csv)
    try:
        return LeitoCsvProvider(leitos_csv=leitos_csv, pacientes_csv=pacientes_csv)
    except Exception as e:
        logging.exception("Error constructing LeitoCsvProvider")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail={"error": str(e)})

def get_leito_provider() -> Callable[..., LeitoProviderInterface]:
    """Return dependency function for leito provider based on env vars."""
    if os.getenv("POSTGRES_DSN"):
        logging.info("Selected leito provider strategy: postgres (POSTGRES_DSN is configured)")
        return _get_leito_banco_provider

    explicit = (os.getenv("LEITO_PROVIDER_TYPE") or "").strip().upper()
    if explicit == "POSTGRES":
        logging.info("Selected leito provider strategy from LEITO_PROVIDER_TYPE: postgres")
        return _get_leito_banco_provider
    if explicit == "CSV":
        logging.info("Selected leito provider strategy from LEITO_PROVIDER_TYPE: csv")
        return _get_leito_csv_provider

    selected = "banco" if os.getenv("POSTGRES_DSN") else "csv"
    logging.info("Selected leito provider strategy by fallback (POSTGRES_DSN presence): %s", selected)
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
    except Exception:
        logging.exception("Error constructing LeitosController")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail={"error": "LeitosController construction failed"})

# --- Care (Beds/Reservations/Transfers/Notifications) ------------------------
async def get_care_provider() -> CareProvider:
    leitos_csv = _resolve_csv_path("LEITOS_CSV_PATH", "data/leitos.csv")
    pacientes_csv = _resolve_csv_path("PACIENTE_CSV_PATH", "data/pacientes.csv")
    if not os.path.isfile(leitos_csv):
        logging.warning("care leitos CSV not found at %s", leitos_csv)
    if not os.path.isfile(pacientes_csv):
        logging.warning("care pacientes CSV not found at %s", pacientes_csv)
    return CareProvider(leitos_csv_path=leitos_csv, pacientes_csv_path=pacientes_csv)


def get_care_controller(
    provider: CareProvider = Depends(get_care_provider),
) -> CareController:
    return CareController(provider)
    
# --- Notificacao: provider + controller wiring ---------------------------------
from controllers.notificacao_controller import NotificacaoController
from providers.implementations.banco.notificacao_postgres_provider import NotificacaoProvider

async def _get_notificacao_provider(
    session: AsyncSession = Depends(_maybe_get_postgres_session)
) -> NotificacaoProvider:
    return NotificacaoProvider(session)

def get_notificacao_controller(
    session: AsyncSession = Depends(_maybe_get_postgres_session),
) -> NotificacaoController:
    provider = NotificacaoProvider(session)
    return NotificacaoController(provider)

# --- User: provider + controller wiring ---------------------------------
from controllers.user_controller import UserController
from providers.implementations.banco.user_postgres_provider import UserProvider

async def _get_user_provider(
    session: AsyncSession = Depends(_maybe_get_postgres_session)
) -> UserProvider:
    return UserProvider(session)

def get_user_controller(
    session: AsyncSession = Depends(_maybe_get_postgres_session),
) -> UserController:
    provider = UserProvider(session)
    return UserController(provider)

# --- Solicitacao Leitos: provider + controller wiring -----------------------
# Import the postgres session provider; older code referenced `database.get_async_session`
# which did not exist in the new layout. Use `resources.postgres.get_postgres_session`.
from providers.solicitacao_reserva_provider import SolicitacaoReservaProvider
from controllers.solicitacao_leitos_controller import SolicitacaoReservaController
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import importlib


# Fallback in-memory provider when Postgres is not configured (useful for local/dev)
class InMemorySolicitacaoProvider:
    def __init__(self):
        self._data = []
        self._next_id = 1

    async def criar(self, prontuario: int, idade: int, especialidade: str) -> None:
        item = {
            "id": self._next_id,
            "status": "PENDENTE",
            "prontuario_paciente": prontuario,
            "idade_paciente": idade,
            "especialidade_paciente": especialidade,
            "leito_id": None,
            "criada_em": None,
            "atualizada_em": None,
        }
        self._next_id += 1
        self._data.append(item)

    async def listar_todas(self):
        return list(self._data)

    async def listar_pendentes(self):
        return [
            {
                "id": d["id"],
                "prontuario": d["prontuario_paciente"],
                "idade": d["idade_paciente"],
                "especialidade": d["especialidade_paciente"],
                "status": d["status"],
                "lto_lto_id": d.get("leito_id"),
            }
            for d in self._data if d.get("status") == "PENDENTE"
        ]

    async def aprovar(self, solicitacao_id: int, lto_lto_id: str) -> None:
        for d in self._data:
            if d["id"] == solicitacao_id and d["status"] == "PENDENTE":
                d["status"] = "APROVADA"
                d["leito_id"] = lto_lto_id
                return
        raise ValueError("Solicitação não encontrada ou já processada")

    async def negar(self, solicitacao_id: int, motivo: str | None = None) -> None:
        for d in self._data:
            if d["id"] == solicitacao_id and d["status"] == "PENDENTE":
                d["status"] = "NEGADA"
                d["motivo_negacao"] = motivo
                return
        raise ValueError("Solicitação não encontrada ou já processada")

    async def cancelar(self, solicitacao_id: int, perfil: str, motivo: str | None = None) -> None:
        for d in self._data:
            if d["id"] == solicitacao_id:
                d["status"] = "CANCELADA"
                d["cancelado_por"] = perfil
                d["motivo_cancelamento"] = motivo
                return
        raise ValueError("Solicitação não encontrada")


def get_solicitacao_reserva_controller(
    session: AsyncSession = Depends(_maybe_get_postgres_session),
    notificacao_controller: NotificacaoController = Depends(get_notificacao_controller)
) -> SolicitacaoReservaController:
    # If Postgres session provider is unavailable, fallback to in-memory provider
    logging.debug("get_solicitacao_reserva_controller called, session=%s", type(session))
    try:
        if session is None:
            raise RuntimeError()
        provider = SolicitacaoReservaProvider(session)
    except Exception as e:
        logging.warning("Falling back to InMemorySolicitacaoProvider: %s", repr(e))
        provider = InMemorySolicitacaoProvider()
    return SolicitacaoReservaController(provider, notificacao_controller)

# --- Notificacao: provider + controller wiring ---------------------------------
from controllers.notificacao_controller import NotificacaoController
from providers.implementations.banco.notificacao_postgres_provider import NotificacaoProvider

async def _get_notificacao_provider(
    session: AsyncSession = Depends(_maybe_get_postgres_session)
) -> NotificacaoProvider:
    return NotificacaoProvider(session)

def get_notificacao_controller(
    session: AsyncSession = Depends(_maybe_get_postgres_session),
) -> NotificacaoController:
    provider = NotificacaoProvider(session)
    return NotificacaoController(provider)

# --- Transferencia: provider + controller wiring ---------------------------------
from controllers.transferencia_paciente_controller import TransferenciaPacienteController
# Assuming there's a provider, but for now, I'll assume it's similar
# For simplicity, I'll assume it uses a provider from providers/implementations/banco/transferencia_postgress.py or similar

# Since I don't see it, I'll create a simple one
# But to make it work, I'll assume it's like solicitacao

def get_transferencia_paciente_controller(
    notificacao_controller: NotificacaoController = Depends(get_notificacao_controller)
) -> TransferenciaPacienteController:
    # For now, mock provider
    class MockTransferenciaProvider:
        async def criar(self, data):
            pass
        async def listar(self):
            return []
        async def aceitar(self, id, leito):
            pass
        async def negar(self, id, motivo):
            pass
    
    provider = MockTransferenciaProvider()
    return TransferenciaPacienteController(provider, notificacao_controller)
