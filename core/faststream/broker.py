from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue


broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)
exchange = RabbitExchange("exchange_chat")
# queue_clients_greeting = RabbitQueue("greeting_with_clients")
# queue_notifying_client_operator = RabbitQueue("notifying_client_operator_connection")
queue_notify_client = RabbitQueue("notify_client")
queue_clients = RabbitQueue("from_clients")
queue_operators = RabbitQueue("from_operators")
