import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Annotated, Optional, Dict, Set

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, Depends
from sqlalchemy import select, update, insert
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket

from core import db_helper
from core.models.ws_connections import WebsocketConnections
from core.websockets.crud import insert_websocket_db

log = logging.getLogger(__name__)

"""

- client_id
- connected_at
- disconnected_at
- ip_address
- user_agent
- is_active

"""


class WebsocketManager:
    def __init__(self):
        self.operators: dict[str, WebSocket] = {}
        self.clients: dict[str, WebSocket] = {}

    async def connect_client(
        self,
        websocket: WebSocket,
        client_id: str,
        ip_address: str,
        user_agent: str,
        is_active: bool,
        session: AsyncSession,
    ):
        await websocket.accept()
        self.clients[client_id] = websocket

        await insert_websocket_db(
            session=session,
            username=client_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=is_active,
            connection_type="client",
        )

    async def connect_operator(
        self,
        websocket: WebSocket,
        operator_id: str,
        ip_address: str,
        user_agent: str,
        is_active: bool,
        session: AsyncSession,
    ):
        await websocket.accept()
        self.operators[operator_id] = websocket

        await insert_websocket_db(
            session=session,
            username=operator_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=is_active,
            connection_type="operator",
        )

    async def send_to_operator(
        self,
        client_id: str,
        message: str,
    ):  # От клиента - оператору
        if self.operators:
            await self.operators.send_json(
                {
                    "type": "client_message",
                    "client_id": client_id,
                    "message": message,
                }
            )

    async def send_to_clients(
        self,
        client_id: str,
        message: str,
    ):

        if client_id in self.clients:
            await self.clients[client_id].send_json(
                {
                    "type": "operator_message",
                    "to_client": client_id,
                    "message": message,
                }
            )
            log.info(
                f"Operator responded to the client: {client_id} message: {message}"
            )

    async def broadcast_to_operators(
        self,
        message: str,
        client: str,
    ):
        for operator in self.operators.values():
            await operator.send_json(
                {
                    "type": "client_message",
                    "message": message,
                    "client": client,
                }
            )

    async def broadcast_to_clients(
        self,
        message: str,
        operator: str,
    ):
        for client in self.clients.values():
            await client.send_json(
                {
                    "type": "operator_message",
                    "message": message,
                    "operator": operator,
                }
            )


manager = WebsocketManager()
