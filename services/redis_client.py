import redis
import json
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'connection_pool'):
            self.connection_pool = None
            self.client = None

    def connect(self, host: str, port: int, db: int = 0, password: Optional[str] = None):
        try:
            self.connection_pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                max_connections=10
            )
            self.client = redis.Redis(connection_pool=self.connection_pool)
            self.client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def get(self, key: str) -> Optional[str]:
        return self.client.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None):
        return self.client.set(key, value, ex=ex)

    def delete(self, key: str):
        return self.client.delete(key)

    def exists(self, key: str) -> bool:
        return self.client.exists(key) > 0

    def hget(self, key: str, field: str) -> Optional[str]:
        return self.client.hget(key, field)

    def hset(self, key: str, mapping: Dict[str, str]) -> int:
        return self.client.hset(key, mapping=mapping)

    def hdel(self, key: str, *fields: str) -> int:
        return self.client.hdel(key, *fields)

    def hgetall(self, key: str) -> Dict[str, str]:
        return self.client.hgetall(key)

    def hincrby(self, key: str, field: str, increment: int = 1) -> int:
        return self.client.hincrby(key, field, increment)

    def sadd(self, key: str, *members: str) -> int:
        return self.client.sadd(key, *members)

    def srem(self, key: str, *members: str) -> int:
        return self.client.srem(key, *members)

    def smembers(self, key: str) -> set:
        return self.client.smembers(key)

    def scard(self, key: str) -> int:
        return self.client.scard(key)

    def sismember(self, key: str, member: str) -> bool:
        return self.client.sismember(key, member)

    def publish(self, channel: str, message: str):
        return self.client.publish(channel, message)

    def subscribe(self, channels):
        return self.client.pubsub(ignore_subscribe_messages=True).subscribe(channels)

    def pipeline(self):
        return self.client.pipeline()

    def close(self):
        if self.connection_pool:
            self.connection_pool.disconnect()

redis_client = RedisClient()
