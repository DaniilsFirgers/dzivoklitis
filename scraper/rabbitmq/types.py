from typing import Callable, Dict, TypedDict


class RabbitMqAction(TypedDict):
    routing_key: str
    queue_name: str
    callback: Callable


class RabbitMqActions(TypedDict):
    add_flat: RabbitMqAction
    delete_flat:  RabbitMqAction
    add_flat_to_favorites:  RabbitMqAction
    delete_flat_from_favorites:  RabbitMqAction
    delete_old_flats:  RabbitMqAction
    send_text_message:  RabbitMqAction
    send_flat_message:  RabbitMqAction


def add_flat_callback(ch, method, properties, body):
    print(f"Processing add_flat: {body}")
    # Your logic here


def delete_flat_callback(ch, method, properties, body):
    print(f"Processing delete_flat: {body}")
    # Your logic here


def add_flat_to_favorites_callback(ch, method, properties, body):
    print(f"Processing add_flat_to_favorites: {body}")
    # Your logic here


def delete_flat_from_favorites_callback(ch, method, properties, body):
    print(f"Processing delete_flat_from_favorites: {body}")
    # Your logic here


def delete_old_flats_callback(ch, method, properties, body):
    print(f"Processing delete_old_flats: {body}")
    # Your logic here


def send_text_message_callback(ch, method, properties, body):
    print(f"Processing send_text_message: {body}")
    # Your logic here


def send_flat_message_callback(ch, method, properties, body):
    print(f"Processing send_flat_message: {body}")
    # Your logic here


actions: RabbitMqActions = {
    "add_flat": {"routing_key": "flat.add", "queue_name": "add_flat", "callback": add_flat_callback},
    "delete_flat": {"routing_key": "flat.delete", "queue_name": "delete_flat", "callback": delete_flat_callback},
    "add_favorite_flat": {"routing_key": "flat.favorite.add", "queue_name": "add_favorite_flat", "callback": add_flat_to_favorites_callback},
    "delete_favorite_flat": {"routing_key": "flat.favorite.delete", "queue_name": "delete_favorite_flat", "callback": delete_flat_from_favorites_callback},
    "delete_old_flats": {"routing_key": "flat.old.delete", "queue_name": "delete_old_flats", "callback": delete_old_flats_callback},
    "send_text_message": {"routing_key": "message.send", "queue_name": "send_text_message", "callback": send_text_message_callback},
    "send_flat_message": {"routing_key": "message.flat.send", "queue_name": "send_flat_message", "callback": send_flat_message_callback},
}
