from helpers.datetime_helper import utcnow

class LeitoSyncJob:
    def __init__(self, banco_aghu_provider, publisher):
        self.banco_aghu = banco_aghu_provider
        self.publisher = publisher
        self._ultima_execucao = utcnow()

    async def executar(self):
        alteracoes = await self.banco_a.listar_alterados(self._ultima_execucao)

        for leito in alteracoes:
            await self.publisher.publicar(dict(leito))

        self._ultima_execucao = utcnow()
