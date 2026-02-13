import time

from app.observability.metrics import record_redis_command


async def redis_get_with_metrics(redis_client, key: str):
    """
    Wrapper for Redis GET command with metrics.

    Usage:
        value = await redis_get_with_metrics(redis_client, "my_key")

    Args:
        redis_client: Async Redis client instance
        key: Redis key to get

    Returns:
        Value from Redis (or None if not found)
    """
    start = time.time_ns()
    try:
        return await redis_client.get(key)
    finally:
        duration_ms = (time.time_ns() - start) / 1e6
        record_redis_command("GET", duration_ms)


async def redis_set_with_metrics(
    redis_client, key: str, value: str, expire: int | None = None
):
    """
    Wrapper for Redis SET command with metrics.

    Usage:
        await redis_set_with_metrics(redis_client, "my_key", "my_value", expire=3600)

    Args:
        redis_client: Async Redis client instance
        key: Redis key to set
        value: Value to set
        expire: Optional expiration time in seconds

    Returns:
        True if set successfully
    """
    start = time.time_ns()
    try:
        if expire:
            return await redis_client.set(key, value, ex=expire)
        return await redis_client.set(key, value)
    finally:
        duration_ms = (time.time_ns() - start) / 1e6
        record_redis_command("SET", duration_ms)


async def redis_delete_with_metrics(redis_client, key: str):
    """
    Wrapper for Redis DELETE command with metrics.

    Usage:
        await redis_delete_with_metrics(redis_client, "my_key")

    Args:
        redis_client: Async Redis client instance
        key: Redis key to delete

    Returns:
        Number of keys deleted
    """
    start = time.time_ns()
    try:
        return await redis_client.delete(key)
    finally:
        duration_ms = (time.time_ns() - start) / 1e6
        record_redis_command("DEL", duration_ms)


async def redis_exists_with_metrics(redis_client, key: str):
    """
    Wrapper for Redis EXISTS command with metrics.

    Usage:
        exists = await redis_exists_with_metrics(redis_client, "my_key")

    Args:
        redis_client: Async Redis client instance
        key: Redis key to check

    Returns:
        True if key exists
    """
    start = time.time_ns()
    try:
        return await redis_client.exists(key)
    finally:
        duration_ms = (time.time_ns() - start) / 1e6
        record_redis_command("EXISTS", duration_ms)
