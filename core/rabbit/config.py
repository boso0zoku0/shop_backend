from typing import Optional
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from pydantic import BaseModel


class RabbitConfig(BaseModel):
    host: str = "localhost"
    port: int = 5672
    login: str = "guest"
    password: str = "guest"
    vhost: str = "/"

    # Для хранения соединений
    _connection: Optional[AbstractRobustConnection] = None
    _channel: Optional[AbstractChannel] = None

    @property
    def url(self) -> str:
        return (
            f"amqp://{self.login}:{self.password}@{self.host}:{self.port}{self.vhost}"
        )

    async def connect(self) -> AbstractChannel:
        """Установить соединение и вернуть channel"""
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self.url)
            self._channel = await self._connection.channel()
            print(f"Connected to RabbitMQ at {self.host}:{self.port}")

        return self._channel

    async def publish_message(self, queue_name: str, message: str):
        """Опубликовать сообщение в очередь"""
        channel = await self.connect()

        # Объявляем очередь (создаст если не существует)
        queue = await channel.declare_queue(
            queue_name, durable=True  # Сохранять при перезапуске RabbitMQ
        )

        # Публикуем сообщение
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=message.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue.name,
        )
        print(f"Message published to queue '{queue_name}': {message}")

    async def consume_messages(self, queue_name: str, callback):
        """Начать потреблять сообщения из очереди"""
        channel = await self.connect()
        queue = await channel.declare_queue(queue_name, durable=True)

        async def message_handler(message: aio_pika.IncomingMessage):
            async with message.process():
                # Вызываем переданную функцию-обработчик
                await callback(message.body.decode())

        # Подписываемся на очередь
        await queue.consume(message_handler)
        print(f"Started consuming from queue '{queue_name}'")

    async def close(self):
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            self._connection = None
            self._channel = None
            print("RabbitMQ connection closed")


config = RabbitConfig()
