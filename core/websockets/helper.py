import json
import logging
from typing import Union
from fastapi import Request
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.websockets import WebSocket, WebSocketDisconnect
from core.websockets.crud import insert_websocket_db, parse
from datetime import datetime

log = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self):
        self.operators: dict[str, WebSocket] = {}
        self.clients: dict[str, WebSocket] = {}

    async def connect_client(
        self,
        websocket: WebSocket,
        client: str,
        ip_address: str,
        user_agent: str,
        is_active: bool,
        user_id: int,
        session: AsyncSession,
    ):
        self.clients[client] = websocket
        # await self.notify_operator_client_connected(client_id)
        await insert_websocket_db(
            session=session,
            username=client,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=is_active,
            connection_type="client",
        )

    async def connect_operator(
        self,
        websocket: WebSocket,
        operator: str,
        user_id: int,
        ip_address: str,
        user_agent: str,
        is_active: bool,
        session: AsyncSession,
    ):
        self.operators[operator] = websocket
        await insert_websocket_db(
            session=session,
            username=operator,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=is_active,
            connection_type="operator",
        )
        log.info(f"✓ Оператор {operator} подключен")

    async def greeting_with_client(
        self,
        client: str,
    ):
        await self.clients[client].send_text(f"Hello, {client}, how can I help you?")

    async def notifying_client(self, client: str, operator: str):
        await self.clients[client].send_text(f"Operator {operator} joined the chat")

    async def send_to_operator(self, client: str, message: str):
        """Отправка сообщения оператору"""
        if not self.operators:
            log.info("✗ Нет подключенных операторов")
            return

        for operator_id, operator_ws in self.operators.items():
            try:
                await operator_ws.send_json(
                    {
                        "type": "client_message",
                        # "action": "connected",
                        "client_id": client,
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                log.info(
                    f"✓ Сообщение от {client} отправлено оператору {operator_id}: {message}"
                )
            except Exception as e:
                log.info(f"✗ Ошибка отправки оператору {operator_id}: {e}")

    async def send_to_client(self, client: str, message: str | dict):
        """Отправка сообщения клиенту"""
        if client in self.clients:
            try:
                await self.clients[client].send_json(
                    {
                        "type": "operator_message",
                        # "action": "connected",
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                log.info(
                    f"✓ Сообщение оператора отправлено клиенту {client}: {message}"
                )
            except Exception as e:
                log.info(f"✗ Ошибка отправки клиенту {client}: {e}")
        else:
            log.info(f"✗ Клиент {client} не найден")

    async def notify_operator_client_connected(self, client: str):
        """Уведомление оператора о новом подключении клиента"""
        for operator_id, operator_ws in self.operators.items():
            try:
                await operator_ws.send_json(
                    {
                        "type": "notify_to_connection",
                        "client_id": client,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except WebSocketDisconnect as e:
                log.warning(e)


manager = WebsocketManager()


broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)

exchange = RabbitExchange("exchange_chat")
queue_clients_greeting = RabbitQueue("greeting_with_clients")
queue_notifying_client_operator = RabbitQueue("notifying_client_operator_connection")
queue_clients = RabbitQueue("from_clients")
queue_operators = RabbitQueue("from_operators")


@broker.subscriber(queue=queue_clients_greeting, exchange=exchange)
async def handler_greeting_with_clients(
    msg: dict,
):

    await manager.greeting_with_client(msg["client"])


@broker.subscriber(queue=queue_notifying_client_operator, exchange=exchange)
async def handler_notifying_client_operator_connection(msg: dict):

    await manager.notifying_client(client=msg["client"], operator=msg["operator"])


@broker.subscriber(queue=queue_clients, exchange=exchange)
async def handler_from_client_to_operator(
    msg: bytes | str | dict,
):
    # data = await parse(msg)
    # action = data.get("action")
    # if action == "connected":
    #     client_id = data.get("client_id")
    #     message = data.get("message")

    await manager.send_to_operator(client=msg["client"], message=msg["message"])


# return


@broker.subscriber(queue=queue_operators, exchange=exchange)
async def handler_from_operator_to_client(msg: bytes | str | dict):
    # data = await parse(msg)
    # action = data.get("action")
    # if action == "connected":
    #     client_id = data.get("client_id")
    #     message = data.get("message")

    await manager.send_to_client(client=msg["client"], message=msg["message"])


# return
