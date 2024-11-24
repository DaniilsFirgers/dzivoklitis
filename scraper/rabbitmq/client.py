import pika
from scraper.config import RabbitMq
import json
from scraper.flat import Flat
from scraper.rabbitmq.types import RabbitMqAction, actions
from threading import Thread, local
from scraper.database import FlatsTinyDb
from scraper.telegram import TelegramBot


class RabbitMqClient:
    def __init__(self, config: RabbitMq, db: FlatsTinyDb, telegram: TelegramBot):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=config.host, port=config.port
        ))
        self.exchange = config.exchange
        self.producer_channel = self.connection.channel()
        self.consumer_channel = self.connection.channel()

        # TODO: implement try-except block for connection

        # declare exchange
        self.producer_channel.exchange_declare(
            exchange=self.exchange, exchange_type="topic", durable=True)
        self.consumer_channel.exchange_declare(
            exchange=self.exchange, exchange_type='topic', durable=True)
        self.db = db
        self.telegram = telegram
        self._actions = actions.values()
        self._local = local()

        # declare queues for producer and consumer
        for action in self._actions:
            # passive - do not create queue if it does not exist
            # durable - queue will survive broker restarts
            # exclusive - the queue is shared across connections
            # auto_delete - the queue is deleted when the last consumer unsubscribes

            # first declare queues
            self.producer_channel.queue_declare(
                queue=action["queue_name"], auto_delete=True)
            self.consumer_channel.queue_declare(
                queue=action["queue_name"], auto_delete=True)
            #  bind queues to exchange
            self.producer_channel.queue_bind(
                exchange=self.exchange, queue=action["queue_name"], routing_key=action["routing_key"])
            self.consumer_channel.queue_bind(
                exchange=self.exchange, queue=action["queue_name"], routing_key=action["routing_key"]

            )

    def publish(self, action: RabbitMqAction, message: Flat | str):
        if isinstance(message, Flat):
            flat_dict = message.to_dict()
            message_body = json.dumps(flat_dict)
            content_type = 'application/json'
        else:
            message_body = str(message)
            content_type = 'text/plain'

        self.connection.add_callback_threadsafe(
            lambda: self.producer_channel.basic_publish(
                exchange=self.exchange,
                routing_key=action["routing_key"],
                body=message_body,
                properties=pika.BasicProperties(
                    content_type=content_type,
                    delivery_mode=2  # Make the message persistent
                )
            )
        )

    def _callback(self, queue_name: str):
        match queue_name:
            case "add_flat":
                def callback(ch, method, properties, body: bytes):
                    print(f" [!] Raw body received: {body}")
                    try:
                        flat_obj = json.loads(body.decode('utf-8'))
                        flat_instance = Flat(**flat_obj)
                        print(f" [x] Received 'add_flat' {flat_instance.id}")
                    except json.JSONDecodeError as e:
                        print(f" [!] Failed to decode JSON: {e}")
                return callback
            case "add_favorite_flat":
                def callback(ch, method, properties, body: bytes):
                    flat_id = body.decode('utf-8')
                    print(
                        f" [x] Received 'add_favorite_flat' {flat_id}")

                return callback
            case "delete_favorite_flat":
                def callback(ch, method, properties, body: bytes):
                    flat_id = body.decode('utf-8')
                    print(
                        f" [x] Received 'delete_favorite_flat' {flat_id}")
                return callback
            case "delete_old_flats":
                def callback(ch, method, properties, body: bytes):
                    try:
                        flat_obj = json.loads(body.decode('utf-8'))
                        flat_instance = Flat(**flat_obj)
                        print(
                            f" [x] Received 'delete_old_flats' {flat_instance.id}")
                    except json.JSONDecodeError as e:
                        print(f" [!] Failed to decode JSON: {e}")
                return callback
            case "send_text_message":
                def callback(ch, method, properties, body: bytes):
                    decoded_body = body.decode('utf-8')
                    self.telegram.send_message(decoded_body)
                return callback
            case "send_flat_message":
                def callback(ch, method, properties, body: bytes):
                    try:
                        flat_obj = json.loads(body.decode('utf-8'))
                        flat_instance = Flat(**flat_obj)
                        self.telegram.send_flat_message(flat_instance)
                    except json.JSONDecodeError as e:
                        print(f" [!] Failed to decode JSON: {e}")
                return callback
        return callback

    def start_consumers(self):
        for action in self._actions:
            self.consumer_channel.basic_consume(
                queue=action["queue_name"],
                on_message_callback=self._callback(action["queue_name"]),
                auto_ack=True
            )

        consumer_thread = Thread(target=self._start_consuming_thread)
        consumer_thread.start()

    def _start_consuming_thread(self):
        self.consumer_channel.start_consuming()

    def close(self):
        self.connection.close()
