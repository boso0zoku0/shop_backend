import asyncio
from typing import Optional, AsyncGenerator, Any

import redis.asyncio as redis


class RedisManager:
    """Менеджер для управления Redis клиентом"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def initialize(self, redis_url: str = "redis://127.0.0.1:6379/1"):
        """Инициализация клиента"""
        self.client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )

        # Проверяем подключение универсально
        try:
            result = self.client.ping()

            # Если result - корутина, await'им её
            if asyncio.iscoroutine(result):
                await result

            print("✅ Redis инициализирован")
            print(f"📊 Redis client: {self.client}")

        except Exception as e:
            print(f"❌ Ошибка при проверке Redis: {e}")
            self.client = None
            raise e

    async def set(self, key: str, value: Any, ex: int = None) -> None:
        """Установить значение с опциональным TTL"""
        if not self.client:
            print("⚠️ Redis клиент не инициализирован")
            return None

        if ex:
            await self.client.setex(key, ex, value)
        else:
            await self.client.set(key, value)

    async def delete(self, key: str) -> None:
        """Удалить ключ"""
        if not self.client:
            return None
        await self.client.delete(key)

    async def close(self):
        """Закрытие клиента"""
        if self.client:
            await self.client.close()
            self.client = None
            print("🔌 Redis закрыт")

    async def get_client(self) -> redis.Redis:
        """Получение клиента"""
        if not self.client:
            raise RuntimeError("Redis не инициализирован")
        return self.client


# Создаем глобальный экземпляр менеджера
redis_manager = RedisManager()


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """FastAPI dependency для Redis клиента"""
    client = await redis_manager.get_client()
    try:
        yield client
    finally:
        # Здесь ничего не закрываем, так как клиент живет всё время
        pass
