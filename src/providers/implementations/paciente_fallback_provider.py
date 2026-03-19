from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException

from providers.interfaces.paciente_provider_interface import PacienteProviderInterface


class PacienteFallbackProvider(PacienteProviderInterface):
    """
    Tenta ler pacientes do provider primário (Postgres) e, em caso de falha
    operacional, recorre ao provider de fallback (CSV).
    """

    def __init__(
        self,
        primary_provider: PacienteProviderInterface,
        fallback_provider: PacienteProviderInterface,
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider

    @staticmethod
    def _should_fallback_http(exc: HTTPException) -> bool:
        # Fallback apenas para falhas de servidor/infra; erros 4xx são funcionais.
        return exc.status_code >= 500

    async def listar_pacientes(self) -> List[Dict[str, Any]]:
        try:
            return await self.primary_provider.listar_pacientes()
        except HTTPException as exc:
            if not self._should_fallback_http(exc):
                raise
            print(f"WARNING: primary paciente provider failed ({exc.status_code}); using CSV fallback.")
            return await self.fallback_provider.listar_pacientes()
        except Exception as exc:
            print(f"WARNING: primary paciente provider raised {type(exc).__name__}; using CSV fallback.")
            return await self.fallback_provider.listar_pacientes()

    async def obter_paciente_por_codigo(self, codigo: int) -> Dict[str, Any]:
        try:
            return await self.primary_provider.obter_paciente_por_codigo(codigo)
        except HTTPException as exc:
            if not self._should_fallback_http(exc):
                raise
            print(
                f"WARNING: primary paciente provider failed ({exc.status_code}) for codigo={codigo}; "
                "using CSV fallback."
            )
            return await self.fallback_provider.obter_paciente_por_codigo(codigo)
        except Exception as exc:
            print(
                f"WARNING: primary paciente provider raised {type(exc).__name__} for codigo={codigo}; "
                "using CSV fallback."
            )
            return await self.fallback_provider.obter_paciente_por_codigo(codigo)
