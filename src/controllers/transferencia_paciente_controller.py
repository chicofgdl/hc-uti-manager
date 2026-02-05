class TransferenciaPacienteController:

    def __init__(self, provider):
        self.provider = provider

    async def criar(self, data: TransferenciaPacienteInput):
        await self.provider.criar(data)

    async def listar(self):
        return await self.provider.listar()

    async def aceitar(self, transferencia_id: int, leito_id: str):
        await self.provider.aceitar(transferencia_id, leito_id)

    async def negar(self, transferencia_id: int, motivo: str | None):
        await self.provider.negar(transferencia_id, motivo)
