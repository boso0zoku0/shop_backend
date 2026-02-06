# managers/connection_manager.py
from typing import Dict
from fastapi import WebSocket


# class ConnectionManager:
#     def __init__(self):
#         self.client_connections: Dict[str, WebSocket] = {}
#         self.operator_connections: Dict[str, WebSocket] = {}
#         self.active_chats: Dict[str, str] = {}  # client_id -> operator_id
#
#     async def connect_client(self, client_id: str, websocket: WebSocket):
#         await websocket.accept()
#         self.client_connections[client_id] = websocket
#
#     async def connect_operator(self, operator_id: str, websocket: WebSocket):
#         await websocket.accept()
#         self.operator_connections[operator_id] = websocket
#
#     async def disconnect_client(self, client_id: str):
#         if client_id in self.client_connections:
#             del self.client_connections[client_id]
#
#     async def disconnect_operator(self, operator_id: str):
#         if operator_id in self.operator_connections:
#             del self.operator_connections[operator_id]
#
#     async def send_to_client(self, client_id: str, message: str):
#         if client_id in self.client_connections:
#             await self.client_connections[client_id].send_text(message)
#
#     async def send_to_operator(self, operator_id: str, message: str):
#         if operator_id in self.operator_connections:
#             await self.operator_connections[operator_id].send_text(message)
#
#     async def assign_chat(self, client_id: str, operator_id: str):
#         self.active_chats[client_id] = operator_id
#
#     async def get_operator_for_client(self, client_id: str) -> str:
#         return self.active_chats.get(client_id)
