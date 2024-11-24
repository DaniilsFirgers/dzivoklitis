from typing import Callable, Dict, TypedDict


class RabbitMqAction(TypedDict):
    routing_key: str
    queue_name: str


class RabbitMqActions(TypedDict):
    add_flat: RabbitMqAction
    delete_flat:  RabbitMqAction
    add_favorite_flat:  RabbitMqAction
    delete_favorite_flat:  RabbitMqAction
    delete_old_flats:  RabbitMqAction
    send_text_message:  RabbitMqAction
    send_flat_message:  RabbitMqAction


actions: RabbitMqActions = {
    "add_flat": {"routing_key": "flat.add", "queue_name": "add_flat"},
    "add_favorite_flat": {"routing_key": "flat.favorite.add", "queue_name": "add_favorite_flat"},
    "delete_favorite_flat": {"routing_key": "flat.favorite.delete", "queue_name": "delete_favorite_flat"},
    "delete_old_flats": {"routing_key": "flat.old.delete", "queue_name": "delete_old_flats"},
    "send_text_message": {"routing_key": "message.send", "queue_name": "send_text_message"},
    "send_flat_message": {"routing_key": "message.flat.send", "queue_name": "send_flat_message"},
}
