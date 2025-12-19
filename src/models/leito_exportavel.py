from typing import TypedDict
from datetime import datetime

class LeitoModel(TypedDict):
    lto_lto_id: str
    status: str
    tipo: str
    alta_solicitada: bool
    prontuario_atual: int | None
    idade_atual: int | None
    especialidade_atual: str | None
    prontuario_proximo: int | None
    idade_proximo: int | None
    especialidade_proximo: str | None
    atualizado_em: datetime