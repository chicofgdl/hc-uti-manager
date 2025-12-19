import json

class LeitoEventPublisher:
    def __init__(self, redis):
        self.redis = redis

    async def publicar(self, evento: dict):
        await self.redis.publish(
            "leitos.atualizados",
            json.dumps(evento, default=str)
        )
