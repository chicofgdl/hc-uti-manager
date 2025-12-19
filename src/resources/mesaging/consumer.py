import json

class LeitoEventConsumer:
    def __init__(self, redis, banco_aghu_provider):
        self.redis = redis
        self.provider = banco_aghu_provider

    async def start(self):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("leitos.atualizados")

        async for msg in pubsub.listen():
            if msg["type"] != "message":
                continue

            evento = json.loads(msg["data"])
            await self.provider.upsert(evento)
