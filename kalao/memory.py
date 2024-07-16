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


def get(
    name: str, type: type = str,
    default: str | int | float | bool | None = None
) -> str | int | float | bool | None:
    value = client.get(name)

    if value is None:
        return default
    elif type is str:
        return value
    elif type is int:
        return int(value)
    elif type is float:
        return float(value)
    elif type is bool:
        return bool(int(value))


def set(name: str, value: str | int | float | bool) -> bool:
    if isinstance(value, bool):
        value = int(value)

    return client.set(name, value)


def mset(mapping: dict[str, str | int | float | bool]) -> bool:
    for key, value in mapping:
        if isinstance(value, bool):
            mapping[key] = int(value)

    return client.mset(mapping)


os.register_at_fork(after_in_child=_reset_client)

_reset_client()
