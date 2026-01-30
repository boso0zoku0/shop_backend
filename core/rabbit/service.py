# services/rabbitmq_service.py
import json
import uuid
from typing import Dict, Optional

from core.rabbit.config import RabbitConfig


class SupportChatRabbitMQ(RabbitConfig):
    async def send_chat_request(self, client_id: str, message: str):
        """Клиент отправляет запрос в поддержку"""
        payload = {
            "type": "chat_request",
            "client_id": client_id,
            "message": message,
            "timestamp": "2024-01-29T10:00:00",
        }
        await self.publish_message("chat_requests", json.dumps(payload))

    async def listen_for_requests(self, operator_id: str):
        """Оператор слушает новые запросы"""

        async def handle_request(msg: str):
            data = json.loads(msg)
            print(f"Operator {operator_id} got request from {data['client_id']}")

            # Отправляем оператору через WebSocket
            # (нужен доступ к connection_manager)

        await self.consume_messages("chat_requests", handle_request)

    async def create_chat_session(self, client_id: str, operator_id: str) -> str:
        """Создать сессию чата"""
        chat_id = str(uuid.uuid4())
        queue_name = f"chat_{chat_id}"

        # Создаем очередь для этого чата
        channel = await self.connect()
        await channel.declare_queue(queue_name, durable=True)

        # Сохраняем связь в Redis/БД
        # await redis.set(f"chat:{chat_id}:client", client_id)
        # await redis.set(f"chat:{chat_id}:operator", operator_id)

        return chat_id

    async def send_chat_message(self, chat_id: str, sender: str, message: str):
        """Отправить сообщение в чат"""
        payload = {
            "chat_id": chat_id,
            "sender": sender,
            "message": message,
            "timestamp": "2024-01-29T10:00:00",
        }
        await self.publish_message(f"chat_{chat_id}", json.dumps(payload))
