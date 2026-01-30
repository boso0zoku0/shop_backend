from mailbox import Message
from typing import Optional
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from pydantic import BaseModel

from typing import Dict
from fastapi import WebSocket


class RabbitConnect:
    host: str = "localhost"
    port: int = 5672
    login: str = "guest"
    password: str = "guest"
    vhost: str = "/"
    # Для хранения соединений
    connection: Optional[AbstractRobustConnection] = None
    channel: Optional[AbstractChannel] = None

    @property
    def url(self) -> str:
        return (
            f"amqp://{self.login}:{self.password}@{self.host}:{self.port}{self.vhost}"
        )

    async def connect(self):
        self.channel = await self.connection.channel()
        print(f"connect: {self.host}:{self.port}")
        return self.channel

    async def publish_message(self, queue_name: str, message: str):
        channel = await self.connect()
        queue = await channel.declare_queue(
            queue_name, durable=True  # Сохранять при перезапуске RabbitMQ
        )
        await channel.default_exchange.publish(
            aio_pika.Message(body=message.encode()), routing_key=queue.name
        )

    async def consume_message(self, queue_name: str, callback):
        channel = await self.connect()
        queue = await channel.declare_queue(queue_name, durable=True)
        exchange = await channel.default_exchange.declare()
