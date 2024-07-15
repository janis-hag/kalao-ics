import os

import redis

import config

client: redis.Redis | None = None


def _reset_client() -> None:
    global client

    if client is not None:
        client.close()

    client = redis.Redis(host=config.Memory.host, port=config.Memory.port,
                         decode_responses=True)

    # client.ping()


def get(name: str) -> str | int | float:
    return client.get(name)


def set(name: str, value: str | int | float) -> bool:
    return client.set(name, value)


def mset(mapping: dict[str, str | int | float]) -> bool:
    return client.mset(mapping)


os.register_at_fork(after_in_child=_reset_client)

_reset_client()
