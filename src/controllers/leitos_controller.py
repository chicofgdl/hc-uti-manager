from models.reserva_leito import ReservaLeitoInput
from typing import List, Dict, Any

class LeitosController:
    def __init__(self, banco_b_provider):
        self.provider = banco_b_provider

    async def listar(self):
        return await self.provider.listar_leitos()
    
    async def reservar(
        self,
        lto_lto_id: str,
        payload: ReservaLeitoInput
    ):
        await self.provider.reservar_leito(
            lto_lto_id=lto_lto_id,
            prontuario=payload.prontuario,
            idade=payload.idade,
            especialidade=payload.especialidade
        )

        return {"message": "Reserva registrada com sucesso"}
    
    async def solicitar_alta(self, leito_id: str):
        await self.provider.solicitar_alta(leito_id)

    async def cancelar_alta(self, leito_id: str):
        await self.provider.cancelar_alta(leito_id) 

    async def listar_leitos_disponiveis_para_reserva(self):
        return await self.provider.listar_leitos_disponiveis_para_reserva()
    
    async def listar_leitos(self) -> List[Dict[str, Any]]:
        return await self.provider.listar_leitos()