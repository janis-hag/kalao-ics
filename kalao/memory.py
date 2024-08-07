import os
import uuid
from enum import Enum

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


def flush():
    client.flushall()


##### Getters


def _convert_value_get(value: str, type: type, default=str | int | float |
                       bool | None) -> str | int | float | bool | None:
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


def get(
    name: str, type: type = str,
    default: str | int | float | bool | None = None
) -> str | int | float | bool | None:
    value = client.get(name)

    return _convert_value_get(value, type, default)


def hget(
    name: str, key: str, type: type = str,
    default: str | int | float | bool | None = None
) -> str | int | float | bool | None:
    value = client.hget(name, key)

    return _convert_value_get(value, type, default)


def mget(keys_mapping: dict[str, type]
         ) -> dict[str, str | int | float | bool | None]:
    keys = list(keys_mapping.keys())

    values = client.mget(keys)

    mapping = {}
    for i, key in enumerate(keys):
        mapping[key] = _convert_value_get(values[i], keys_mapping[key])

    return mapping


def hmget(name: str, keys_mapping: dict[str, type]
          ) -> dict[str, str | int | float | bool | None]:
    keys = list(keys_mapping.keys())

    values = client.hmget(name, keys)

    mapping = {}
    for i, key in enumerate(keys):
        mapping[key] = _convert_value_get(values[i], keys_mapping[key])

    return mapping


##### Setters


def _convert_value_set(value: str | int | float | bool | None
                       ) -> str | int | float | None:
    if isinstance(value, bool):
        return int(value)
    elif isinstance(value, Enum):
        return value.value
    else:
        return value


def set(name: str, value: str | int | float | bool) -> bool:
    return client.set(name, _convert_value_set(value))


def hset(name: str, key: str, value: str | int | float | bool) -> int:
    return client.hset(name, key, _convert_value_set(value))


def mset(mapping: dict[str, str | int | float | bool]) -> bool:
    for key, value in mapping.items():
        mapping[key] = _convert_value_set(value)

    return client.mset(mapping)


def hmset(name: str, mapping: dict[str, str | int | float | bool]) -> int:
    for key, value in mapping.items():
        mapping[key] = _convert_value_set(value)

    return client.hset(name, mapping=mapping)


def hdel(name: str, *keys: str) -> int:
    return client.hdel(name, *keys)


##### Locks


def locked(key: str) -> bool:
    return client.get(key) is not None


def lock(key: str) -> str | None:
    secret = str(uuid.uuid4())

    success = client.set(key, secret, nx=True)

    if success:
        return secret
    else:
        return None


def unlock(key: str, secret: str = '', force: bool = False) -> bool:
    if force or client.get(key) == secret:
        client.delete(key)
        return True
    else:
        return False


os.register_at_fork(after_in_child=_reset_client)

_reset_client()
