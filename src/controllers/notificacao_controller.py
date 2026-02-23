from typing import List, Dict, Any
from providers.implementations.banco.notificacao_postgres_provider import NotificacaoProvider


class NotificacaoController:

    def __init__(self, provider: NotificacaoProvider):
        self.provider = provider

    async def criar(self, tipo: str, mensagem: str, role_destino: str) -> None:
        await self.provider.criar(
            tipo=tipo,
            mensagem=mensagem,
            role_destino=role_destino
        )

    async def listar_por_role(self, role: str) -> List[Dict[str, Any]]:
        return await self.provider.listar_por_role(role)

    async def marcar_como_lida(self, notificacao_id: int) -> None:
        await self.provider.marcar_como_lida(notificacao_id)