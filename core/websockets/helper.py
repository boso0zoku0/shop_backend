import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.faststream.broker import broker, exchange, queue_notify_client
from core.models import PendingMessages
from core.websockets.crud import insert_websocket_db
from datetime import datetime

log = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self):
        self.operators: dict[str, WebSocket] = {}
        self.clients: dict[str, WebSocket] = {}
        self.connection_client_operator: dict[str, str] = {}  # client, operator

    async def get_free_operator(self):
        busy_operators = set(self.connection_client_operator.values())
        for operator in self.operators.keys():
            if operator not in busy_operators:
                return operator
        return None

    async def connect_client(
        self,
        websocket: WebSocket,
        client: str,
        ip_address: str,
        user_agent: str,
        is_active: bool,
        user_id: int,
        session: AsyncSession,
        is_advertising: bool = False,
    ):
        self.clients[client] = websocket
        await self.clients[client].send_json(
            {"type": "greeting", "message": f"Hello {client} how can I help you?"}
        )
        free_operator = await self.get_free_operator()
        if free_operator is None:
            log.info("No free operator")
        self.connection_client_operator[client] = free_operator

        if not is_advertising:
            await insert_websocket_db(
                session=session,
                username=client,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=is_active,
                connection_type="client",
            )
        else:
            await insert_websocket_db(
                session=session,
                username=client,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=is_active,
                connection_type="client",
            )
            stmt = (
                select(PendingMessages)
                .where(PendingMessages.user_id == user_id)
                .limit(1)
            )
            res = await session.execute(stmt)
            message = res.scalar_one_or_none()
            if not message:
                return
            await broker.publish(
                message={
                    "type": "advertising",
                    "client": client,
                    "message": message.message,
                },
                queue=queue_notify_client,
                exchange=exchange,
            )
            await session.delete(message)

    async def connect_operator(
        self,
        websocket: WebSocket,
        operator: str,
        client: str,
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
        if client in self.clients:
            await self.clients.get(client).send_json(
                {"type": "notify", "message": f"Operator {operator} joined the chat"}
            )
            self.connection_client_operator[client] = operator

            log.info(f"✓ Оператор {operator} подключен")

    async def greeting_with_client(self, client: str):
        await self.clients.get(client).send_json(
            {"type": "greeting", "message": f"Hello, {client}, how can I help you?"}
        )

    async def send_to_operator(self, client: str, message: str):
        operator = self.connection_client_operator.get(client)
        if operator is None:
            log.info("Нет оператора для клиента")
        op_ws = self.operators.get(operator)
        if op_ws is None:
            log.info("Оператор не подключен")
        try:
            await self.operators.get(operator).send_json(
                {
                    "type": "client_message",
                    "client": client,
                    "operator": operator,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            log.info(f"✗ Ошибка отправки {client} -> {operator}")

    async def send_to_client(self, client: str, operator: str, message: str):
        """Отправка сообщения клиенту"""
        if self.connection_client_operator.get(client) != operator:
            log.info("Отсутствует соединение")
            return
        try:
            await self.clients.get(client).send_json(
                {
                    "type": "operator_message",
                    "operator": operator,
                    "client": client,
                    "message": message,
                }
            )
            log.info(f"✓ Сообщение отправлено клиенту {client}: {message}")
        except Exception as e:
            log.info(f"✗ Ошибка отправки {operator} -> {client}")

    # async def notify_operator_client_connected(self, client: str) -> None:
    #     """Уведомление оператора о новом подключении клиента"""
    #     for operator_id, operator_ws in self.operators.items():
    #         try:
    #             await operator_ws.send_json(
    #                 {
    #                     "type": "notify_to_connection",
    #                     "client_id": client,
    #                     "timestamp": datetime.now().isoformat(),
    #                 }
    #             )
    #         except WebSocketDisconnect as e:
    #             log.warning(e)

    async def advertising_to_client(self, client: str, message: str):
        await self.clients.get(client).send_json(
            {
                "type": "advertising",
                "client": client,
                "message": message,
            }
        )


manager = WebsocketManager()
