from controllers.notificacao_controller import NotificacaoController
from models.transferencia_paciente import TransferenciaPacienteInput

class TransferenciaPacienteController:

    def __init__(self, provider, notificacao_controller: NotificacaoController):
        self.provider = provider
        self.notificacao_controller = notificacao_controller

    async def criar(self, data: TransferenciaPacienteInput):
        await self.provider.criar(data)
        await self.notificacao_controller.criar(
            tipo="solicitacao_transferencia",
            mensagem="Nova solicitação de transferência de paciente pendente",
            role_destino="enfermeiro_uti"
        )

    async def listar(self):
        return await self.provider.listar()

    async def aceitar(self, transferencia_id: int, leito_id: str):
        await self.provider.aceitar(transferencia_id, leito_id)
        await self.notificacao_controller.criar(
            tipo="transferencia_aceita",
            mensagem=f"Transferência {transferencia_id} aceita, paciente pronto para ser transferido",
            role_destino="enfermeiro_cirurgia"
        )

    async def negar(self, transferencia_id: int, motivo: str | None):
        await self.provider.negar(transferencia_id, motivo)
        await self.notificacao_controller.criar(
            tipo="transferencia_negada",
            mensagem=f"Transferência {transferencia_id} negada",
            role_destino="enfermeiro_cirurgia"
        )
