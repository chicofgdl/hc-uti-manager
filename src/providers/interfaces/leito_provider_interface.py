from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LeitoProviderInterface(ABC):
    """Interface (contrato) para provedores de dados de leitos."""

    @abstractmethod
    async def listar_leitos(self) -> List[Dict[str, Any]]:
        """Deve retornar uma lista de leitos"""
        pass

    # @abstractmethod
    # async def obter_leito_por_codigo(self, codigo: int) -> Dict[str, Any]:
    #     """Deve retornar um único leito pelo seu código"""
    #     pass
    
    @abstractmethod
    async def solicitar_alta(self, leito_id: int) -> None:
        pass

    @abstractmethod
    async def cancelar_alta(self, leito_id: int) -> None:
        pass

    @abstractmethod
    async def listar_leitos_disponiveis_para_reserva(self) -> List[Dict[str, Any]]:
        pass