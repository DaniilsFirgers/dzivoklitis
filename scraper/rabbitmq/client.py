import pika
from scraper.config import RabbitMq
import json
from scraper.rabbitmq.types import RabbitMqAction, actions
from threading import Thread
from scraper.database import FlatsTinyDb


class RabbitMqClient:
    def __init__(self, config: RabbitMq, db: FlatsTinyDb):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=config.host, port=config.port
        ))
        self.exchange = config.exchange
        self.producer_channel = self.connection.channel()
        self.consumer_channel = self.connection.channel()

        # declare exchange
        self.producer_channel.exchange_declare(
            exchange=self.exchange, exchange_type="topic", durable=True)
        self.consumer_channel.exchange_declare(
            exchange=self.exchange, exchange_type='topic', durable=True)
        self.db = db
        self._actions = actions.values()
        # declare queues for producer and consumer
        for action in self._actions:
            # passive - do not create queue if it does not exist
            # durable - queue will survive broker restarts
            # exclusive - the queue is shared across connections
            # auto_delete - the queue is deleted when the last consumer unsubscribes

            # first declare queues
            self.producer_channel.queue_declare(
                queue=action["queue_name"], passive=True, durable=False, exclusive=False, auto_delete=True)
            self.consumer_channel.queue_declare(
                queue=action["queue_name"], passive=True, durable=False, exclusive=False, auto_delete=True)
            #  bind queues to exchange
            self.producer_channel.queue_bind(
                exchange=self.exchange, queue=action["queue_name"], routing_key=action["routing_key"])
            self.consumer_channel.queue_bind(
                exchange=self.exchange, queue=action["queue_name"], routing_key=action["routing_key"]
            )

    def publish(self, action: RabbitMqAction, message: dict | str):
        content_type = 'application/json' if isinstance(
            message, dict) else 'text/plain'
        self.producer_channel.basic_publish(
            exchange=self.exchange,
            routing_key=action["routing_key"],
            body=json.dumps(message),
            properties=pika.BasicProperties(
                content_type=content_type,
                delivery_mode=2,  # make message persistent
            )
        )

    def start_consumers(self):
        for action in self._actions:
            self.consumer_channel.basic_consume(
                queue=action["routing_key"],
                on_message_callback=action["callback"],
                auto_ack=True
            )

        consumer_thread = Thread(target=self._start_consuming_thread)
        consumer_thread.start()

    def _start_consuming_thread(self):
        self.consumer_channel.start_consuming()

    def close(self):
        self.connection.close()
