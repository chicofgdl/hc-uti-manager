from abc import ABC, abstractmethod
from typing import List, Dict

class SolicitacaoReservaProviderInterface(ABC):

    @abstractmethod
    async def criar(
        self,
        prontuario: int,
        idade: int,
        especialidade: str
    ) -> None:
        pass

    @abstractmethod
    async def listar_pendentes(self) -> List[Dict]:
        pass

    @abstractmethod
    async def aprovar(
        self,
        solicitacao_id: int,
        lto_lto_id: str
    ) -> None:
        pass

    @abstractmethod
    async def negar(
        self,
        solicitacao_id: int,
        motivo: str
    ) -> None:
        pass
