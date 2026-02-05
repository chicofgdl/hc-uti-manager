from models.reserva_leito import SolicitacaoReservaInput
from providers.solicitacao_reserva_provider import SolicitacaoReservaProvider


class SolicitacaoReservaController:

    def __init__(self, provider: SolicitacaoReservaProvider):
        self.provider = provider

    async def criar(self, data: SolicitacaoReservaInput) -> None:
        await self.provider.criar(
            prontuario=data["prontuario"],
            idade=data["idade"],
            especialidade=data["especialidade"]
        )

    async def listar_todas(self):
        return await self.provider.listar_todas()

    async def listar_pendentes(self):
        return await self.provider.listar_pendentes()

    async def aprovar(self, solicitacao_id: int, lto_lto_id: str) -> None:
        await self.provider.aprovar(solicitacao_id, lto_lto_id)

    async def negar(self, solicitacao_id: int, motivo: str | None = None) -> None:
        await self.provider.negar(solicitacao_id, motivo)

    async def cancelar(
        self,
        solicitacao_id: int,
        perfil: str,
        motivo: str | None = None
    ) -> None:
        await self.provider.cancelar(
            solicitacao_id=solicitacao_id,
            perfil=perfil,
            motivo=motivo
        )
        