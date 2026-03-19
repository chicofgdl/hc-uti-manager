from models.reserva_leito import SolicitacaoReservaInput
from providers.solicitacao_reserva_provider import SolicitacaoReservaProvider
from controllers.notificacao_controller import NotificacaoController
import logging


class SolicitacaoReservaController:

    def __init__(self, provider: SolicitacaoReservaProvider, notificacao_controller: NotificacaoController):
        self.provider = provider
        self.notificacao_controller = notificacao_controller

    async def _notify_safely(self, tipo: str, mensagem: str, role_destino: str) -> None:
        try:
            await self.notificacao_controller.criar(
                tipo=tipo,
                mensagem=mensagem,
                role_destino=role_destino
            )
        except Exception:
            logging.exception("Falha ao registrar notificacao '%s' para '%s'", tipo, role_destino)

    async def criar(self, data: SolicitacaoReservaInput) -> int:
        created_id = await self.provider.criar(
            prontuario=data["prontuario"],
            idade=data["idade"],
            especialidade=data["especialidade"]
        )
        await self._notify_safely(
            tipo="solicitacao_reserva",
            mensagem="Nova solicitação de reserva de leito pendente",
            role_destino="enfermeiro_uti"
        )
        return created_id

    async def listar_todas(self):
        return await self.provider.listar_todas()

    async def listar_pendentes(self):
        return await self.provider.listar_pendentes()

    async def aprovar(self, solicitacao_id: int, lto_lto_id: str) -> None:
        await self.provider.aprovar(solicitacao_id, lto_lto_id)
        await self._notify_safely(
            tipo="reserva_aprovada",
            mensagem=f"Solicitação de reserva {solicitacao_id} aprovada",
            role_destino="enfermeiro_cirurgia"
        )

    async def negar(self, solicitacao_id: int, motivo: str | None = None) -> None:
        await self.provider.negar(solicitacao_id, motivo)
        await self._notify_safely(
            tipo="reserva_negada",
            mensagem=f"Solicitação de reserva {solicitacao_id} negada",
            role_destino="enfermeiro_cirurgia"
        )

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
        # Notificar o outro role
        if "uti" in perfil.lower():
            role_destino = "enfermeiro_cirurgia"
        else:
            role_destino = "enfermeiro_uti"
        await self._notify_safely(
            tipo="reserva_cancelada",
            mensagem=f"Solicitação de reserva {solicitacao_id} cancelada",
            role_destino=role_destino
        )
        
