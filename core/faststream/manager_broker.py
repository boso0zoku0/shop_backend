# from faststream import FastStream
# from faststream.rabbit import RabbitBroker
# from faststream import FastStream, Logger
# from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

# from core.websockets import manager
#
# broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
# app = FastStream(broker)
#
# exchange = RabbitExchange("exchange_chat")
# queue_clients = RabbitQueue("from_clients")
# queue_operators = RabbitQueue("from_operators")
#
#
# @broker.subscriber(queue=queue_clients, exchange=exchange)
# async def handler_from_client_to_operator(msg: dict):
#     manager.send_to_operator(msg["client_id"], msg["message"])
#     client_id = msg["client_id"]
#     message = msg["message"]
#
#     # 2. Отправляем оператору
#     await manager.send_to_operator(
#         client_id=client_id,  # Кому адресовано
#         message={
#             "type": "client_message",
#             "client_id": client_id,
#             "message": message["message"],
#             "timestamp": message["timestamp"],
#         },
#     )
#
#
# @broker.subscriber(queue=queue_operators, exchange=exchange)
# async def handler_from_operator_to_client(msg: dict):
#     manager.send_to_client(msg["client_id"], msg["message"])
