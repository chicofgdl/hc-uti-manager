try:
    from typing_extensions import TypedDict
except Exception:
    from typing import TypedDict
from datetime import datetime


class SolicitacaoReservaInput(TypedDict):
    prontuario: str | int
    idade: int
    especialidade: str

# Backwards-compatible aliases: some modules expect the older name
# `ReservaLeitoInput`/`ReservaLeitoOutput` so we provide simple aliases
ReservaLeitoInput = SolicitacaoReservaInput


class SolicitacaoReservaOutput(TypedDict):
    id: int
    prontuario: int
    idade: int
    especialidade: str
    status: str
    lto_lto_id: str | None
    criada_em: datetime
    atualizada_em: datetime

ReservaLeitoOutput = SolicitacaoReservaOutput

class SolicitacaoReservaNegacaoInput(TypedDict, total=False):
    motivo: str
