import redis.asyncio as redis

def get_redis(redis_url: str):
    return redis.from_url(redis_url, decode_responses=True)
