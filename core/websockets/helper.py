import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket, WebSocketDisconnect

from core import db_helper
from core.crud import get_list_games, get_list_genres
from core.faststream.broker import broker, exchange, queue_notify_client
from core.models import PendingMessages
from core.models.ws_history_message import WebsocketMessageHistory, TypeMessage
from core.websockets.crud import (
    insert_websocket_db,
    insert_message_history,
    get_user_by_name,
)

log = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self):
        self.operators: dict[str, WebSocket] = {}
        self.clients: dict[str, WebSocket] = {}
        self.clients_asks_help: dict = {}
        self.timeout_busy_operator: defaultdict[str, dict[str, datetime]] = defaultdict(
            dict
        )

    async def send_to_operator(
        self,
        session: AsyncSession,
        client: str,
        operator: str,
        message: str,
    ):
        if operator == "":
            from_user_id = await get_user_by_name(client, session)
            await insert_message_history(
                session=session,
                from_user_id=from_user_id,
                message=message,
                type_message=TypeMessage.client.value,
            )
            pass
        else:
            await self.operators[operator].send_json(
                {
                    "type": "client_message",
                    "from": client,
                    "to": operator,
                    "message": message,
                }
            )
            from_user_id = await get_user_by_name(client, session)
            to_user_id = await get_user_by_name(operator, session)
            await insert_message_history(
                session=session,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                message=message,
                type_message=TypeMessage.client.value,
            )
            log.info(f"Сообщение отправлено оператору: {operator}")

    async def send_to_client(
        self,
        session: AsyncSession,
        client: str,
        operator: str,
        message: str,
    ):

        try:
            self.timeout_busy_operator[operator][client] = datetime.now()
            print(f"BUSY: {self.timeout_busy_operator}")
            await self.busy_operator_clear(operator)
            await self.clients[client].send_json(
                {
                    "type": "operator_message",
                    "from": operator,
                    "to": client,
                    "message": message,
                }
            )
            from_user_id = await get_user_by_name(operator, session)
            to_user_id = await get_user_by_name(client, session)
            await insert_message_history(
                session=session,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                message=message,
                type_message=TypeMessage.operator.value,
            )

            log.info(f"✓ Сообщение отправлено клиенту {client}: {message}")
        except Exception as e:
            log.info(f"✗ Ошибка отправки {operator} -> {client}")

    async def disconnect_client(self, client: str):
        try:
            await self.notify_disconnect_to_operators(client)
            if client in self.clients:
                self.clients.pop(client)
                del self.clients_asks_help[client]
                log.info(f"✓ Клиент {client} удален из self.clients")
            for operator, clients_dict in self.timeout_busy_operator.items():
                if client in clients_dict:
                    clients_dict.pop(client)
                    log.info(f"  → Удален из оператора {operator}")
            if hasattr(self, "client_operators"):
                self.client_operators.pop(client, None)
        except Exception as e:
            log.error(f"✗ Ошибка при отключении клиента {client}: {e}")

    async def notify_disconnect_to_operators(self, client: str):
        busy_operators = set(self.timeout_busy_operator.keys())
        for op in self.operators.keys():
            # для отладки not убрал, т.к отработает если только время пройдет
            if op in busy_operators:
                log.info(f"Оповещение оператора об отключении клиента")

                await self.operators[op].send_json(
                    {
                        "type": "notify_disconnect",
                        "from": client,
                    }
                )

    async def busy_operator_clear(self, operator: str):
        """
        Убрать клиента из связки оператор-клиенты, если оператор давно ему не отвечал
        """
        if operator in self.timeout_busy_operator:
            for client, timeout in self.timeout_busy_operator[operator].items():
                if timeout + timedelta(minutes=1) < datetime.now():
                    self.timeout_busy_operator[operator].pop(client)

    async def notify_connect_to_operators(
        self,
        client: str,
    ):
        busy_operators = set(self.timeout_busy_operator.keys())
        for op in self.operators.keys():
            # для отладки not убрал, т.к отработает если только время пройдет
            if op in busy_operators:

                await self.operators[op].send_json(
                    {
                        "type": "notify_connect",
                        "from": client,
                        "to": op,
                    }
                )

    async def notify_connect_to_client(self, client: str, operator: str):
        await self.clients[client].send_json(
            {
                "type": "notify_connect_to_client",
                "from": operator,
                "to": client,
                "message": f"Operator {operator} has joined chat",
            }
        )

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
        await self.init_communication_with_client(client)

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
            await self.advertising_to_client(
                client=client,
                message=message.message,
            )
            await session.delete(message)

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

        self.timeout_busy_operator[operator] = {}
        # Если по ключу оператор пусто - значит можно считать оператора НЕ занятым
        log.info(
            f"Оператор добавлен в список для помощи клиентам {dict(self.timeout_busy_operator)}"
        )
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

    async def get_clients(self):
        return list(self.clients_asks_help.keys())

    async def sender_bot(
        self, client: str, message: str, session: AsyncSession, websocket: WebSocket
    ):

        triggers_operator = {"help me", "call the operator"}
        triggers_bot = {
            "View the movie catalog": lambda: get_list_games(session),
            "View the genre catalog": lambda: get_list_genres(session),
            "Find out the creator of the website": "The creator comes from a small town. The site was created in 2026 as part of a single developer",
            "Call the operator with command - 'help me'": "The operator is already rushing to you",
        }
        # Проверка на вызов оператора
        if any(trigger in message for trigger in triggers_operator):
            await self.clients[client].send_json(
                {
                    "type": "bot_message",
                    "message": "The operator is already rushing to you",
                }
            )
            self.clients_asks_help[client] = message
            await self.notify_connect_to_operators(client)
            return True
        # Проверка на остальные команды в боте
        for question, response in triggers_bot.items():
            if question in message:
                if callable(response):
                    answer = await response()
                else:
                    answer = response
                await self.clients[client].send_json(
                    {
                        "type": "bot_message",
                        "message": answer,
                    }
                )
                return True
        return False

    async def init_communication_with_client(self, client: str):
        await self.clients[client].send_json(
            {
                "type": "greeting",
                "message": [
                    f"Hello, {client}, how can I help you?",
                    "1)View the movie catalog",
                    "2) View the genre catalog",
                    "3) Find out the creator of the website",
                    "4) Call the operator with command - 'help me'",
                ],
            }
        )

    async def advertising_to_client(self, client: str, message: str):
        await self.clients.get(client).send_json(
            {
                "type": "advertising",
                "to": client,
                "message": message,
            }
        )

    async def send_media_to_client(
        self,
        session: AsyncSession,
        operator: str,
        client: str,
        file_url: str,
        mime_type: str,
        message: str = "",
    ):
        if client == "":
            from_user_id = await get_user_by_name(operator, session)
            await insert_message_history(
                session=session,
                from_user_id=from_user_id,
                message=message,
                type_message=TypeMessage.media.value,
                file_url=file_url,
                mime_type=mime_type,
            )
        else:
            await self.clients[client].send_json(
                {
                    "type": "media",
                    "from": operator,
                    "to": client,
                    "message": message,
                    "file_url": file_url,
                    "mime_type": mime_type,
                }
            )
            from_user_id = await get_user_by_name(operator, session)
            to_user_id = await get_user_by_name(client, session)
            await insert_message_history(
                session=session,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                message=message,
                type_message=TypeMessage.media.value,
                file_url=file_url,
                mime_type=mime_type,
            )

    async def send_media_to_operator(
        self,
        session: AsyncSession,
        client: str,
        operator: str,
        file_url: str,
        mime_type: str,
        message: str = "",
    ):

        if operator == "":
            from_user_id = await get_user_by_name(client, session)
            await insert_message_history(
                session=session,
                from_user_id=from_user_id,
                message=message,
                type_message=TypeMessage.media.value,
                file_url=file_url,
                mime_type=mime_type,
            )
        else:
            await self.operators[operator].send_json(
                {
                    "type": "media",
                    "from": client,
                    "to": operator,
                    "message": message,
                    "file_url": file_url,
                    "mime_type": mime_type,
                }
            )
            from_user_id = await get_user_by_name(client, session)
            to_user_id = await get_user_by_name(operator, session)
            await insert_message_history(
                session=session,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                message=message,
                type_message=TypeMessage.media.value,
                file_url=file_url,
                mime_type=mime_type,
            )


manager = WebsocketManager()
