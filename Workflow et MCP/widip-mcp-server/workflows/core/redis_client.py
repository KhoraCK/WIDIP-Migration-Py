"""
Redis Client - Async Redis client for cache and state management
"""

import json
from typing import Any, Optional

import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class RedisClient:
    """
    Async Redis client for WIDIP workflows.

    Handles:
    - Cache operations (GET, SET, DELETE)
    - State management (health status, diagnostic cache)
    - Pub/Sub for real-time updates
    - SETNX for mutex/locks
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        db: int = 0,
        decode_responses: bool = True,
    ):
        """
        Initialize Redis client.

        Args:
            url: Redis connection URL
            db: Database number
            decode_responses: Decode responses to strings
        """
        self.url = url
        self.db = db
        self.decode_responses = decode_responses
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._client is None:
            self._client = redis.from_url(
                self.url,
                db=self.db,
                decode_responses=self.decode_responses,
            )
        return self._client

    async def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None

    # ==================== Basic Operations ====================

    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis.

        Args:
            key: Redis key

        Returns:
            Value or None if not found
        """
        client = await self._get_client()
        try:
            return await client.get(key)
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: str,
        ex: int = None,
        px: int = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set a value in Redis.

        Args:
            key: Redis key
            value: Value to set
            ex: Expire time in seconds
            px: Expire time in milliseconds
            nx: Only set if key does not exist
            xx: Only set if key exists

        Returns:
            True if set successfully
        """
        client = await self._get_client()
        try:
            result = await client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
            return bool(result)
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.

        Args:
            key: Redis key

        Returns:
            True if deleted
        """
        client = await self._get_client()
        try:
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.error("redis_delete_error", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: Redis key

        Returns:
            True if exists
        """
        client = await self._get_client()
        try:
            return await client.exists(key) > 0
        except Exception as e:
            logger.error("redis_exists_error", key=key, error=str(e))
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key.

        Args:
            key: Redis key
            seconds: TTL in seconds

        Returns:
            True if expiration set
        """
        client = await self._get_client()
        try:
            return await client.expire(key, seconds)
        except Exception as e:
            logger.error("redis_expire_error", key=key, error=str(e))
            return False

    async def ttl(self, key: str) -> int:
        """
        Get TTL of a key.

        Args:
            key: Redis key

        Returns:
            TTL in seconds, -1 if no expiry, -2 if not found
        """
        client = await self._get_client()
        try:
            return await client.ttl(key)
        except Exception as e:
            logger.error("redis_ttl_error", key=key, error=str(e))
            return -2

    # ==================== JSON Operations ====================

    async def get_json(self, key: str) -> Optional[Any]:
        """
        Get a JSON value from Redis.

        Args:
            key: Redis key

        Returns:
            Parsed JSON or None
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning("redis_invalid_json", key=key)
                return None
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ex: int = None,
    ) -> bool:
        """
        Set a JSON value in Redis.

        Args:
            key: Redis key
            value: Value to serialize as JSON
            ex: Expire time in seconds

        Returns:
            True if set successfully
        """
        try:
            json_value = json.dumps(value, default=str)
            return await self.set(key, json_value, ex=ex)
        except Exception as e:
            logger.error("redis_set_json_error", key=key, error=str(e))
            return False

    # ==================== Lock Operations (SETNX) ====================

    async def acquire_lock(
        self,
        lock_name: str,
        ttl_seconds: int = 60,
        value: str = "locked",
    ) -> bool:
        """
        Acquire a distributed lock using SETNX.

        Args:
            lock_name: Lock key name
            ttl_seconds: Lock TTL (auto-release)
            value: Lock value

        Returns:
            True if lock acquired
        """
        key = f"lock:{lock_name}"
        return await self.set(key, value, ex=ttl_seconds, nx=True)

    async def release_lock(self, lock_name: str) -> bool:
        """
        Release a distributed lock.

        Args:
            lock_name: Lock key name

        Returns:
            True if released
        """
        key = f"lock:{lock_name}"
        return await self.delete(key)

    async def is_locked(self, lock_name: str) -> bool:
        """
        Check if lock is held.

        Args:
            lock_name: Lock key name

        Returns:
            True if locked
        """
        key = f"lock:{lock_name}"
        return await self.exists(key)

    # ==================== Health Status Operations ====================

    async def get_health_status(self, service: str) -> str:
        """
        Get health status of a service.

        Args:
            service: Service name (e.g., 'glpi')

        Returns:
            Status: 'ok', 'degraded', 'down', or 'unknown'
        """
        key = f"{service}_health_status"
        status = await self.get(key)
        return status or "unknown"

    async def set_health_status(
        self,
        service: str,
        status: str,
        ttl_seconds: int = 60,
    ) -> bool:
        """
        Set health status of a service.

        Args:
            service: Service name
            status: Status value
            ttl_seconds: TTL (default 60s)

        Returns:
            True if set
        """
        key = f"{service}_health_status"
        return await self.set(key, status, ex=ttl_seconds)

    # ==================== Diagnostic Cache ====================

    async def get_diagnostic_cache(
        self,
        device_name: str,
        date: str,
    ) -> Optional[dict]:
        """
        Get cached diagnostic for a device.

        Args:
            device_name: Device identifier
            date: Date string (YYYY-MM-DD)

        Returns:
            Cached diagnostic or None
        """
        key = f"observium_diag_{device_name}_{date}"
        return await self.get_json(key)

    async def set_diagnostic_cache(
        self,
        device_name: str,
        date: str,
        diagnostic: dict,
        ttl_seconds: int = 1200,  # 20 minutes
    ) -> bool:
        """
        Cache diagnostic result for a device.

        Args:
            device_name: Device identifier
            date: Date string (YYYY-MM-DD)
            diagnostic: Diagnostic data
            ttl_seconds: TTL (default 20 min)

        Returns:
            True if cached
        """
        key = f"observium_diag_{device_name}_{date}"
        return await self.set_json(key, diagnostic, ex=ttl_seconds)

    # ==================== Alert Flags ====================

    async def is_alert_sent(self, alert_type: str) -> bool:
        """
        Check if an alert has been sent recently.

        Args:
            alert_type: Type of alert (e.g., 'glpi_down')

        Returns:
            True if alert was sent recently
        """
        key = f"{alert_type}_alert_sent"
        return await self.exists(key)

    async def mark_alert_sent(
        self,
        alert_type: str,
        ttl_seconds: int = 300,  # 5 minutes
    ) -> bool:
        """
        Mark an alert as sent (anti-spam).

        Args:
            alert_type: Type of alert
            ttl_seconds: How long to suppress (default 5 min)

        Returns:
            True if marked
        """
        key = f"{alert_type}_alert_sent"
        return await self.set(key, "sent", ex=ttl_seconds)

    async def clear_alert_sent(self, alert_type: str) -> bool:
        """
        Clear alert sent flag.

        Args:
            alert_type: Type of alert

        Returns:
            True if cleared
        """
        key = f"{alert_type}_alert_sent"
        return await self.delete(key)

    # ==================== Pub/Sub ====================

    async def publish(self, channel: str, message: Any) -> int:
        """
        Publish a message to a channel.

        Args:
            channel: Channel name
            message: Message (will be JSON serialized if dict)

        Returns:
            Number of subscribers that received the message
        """
        client = await self._get_client()
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message, default=str)
            return await client.publish(channel, message)
        except Exception as e:
            logger.error("redis_publish_error", channel=channel, error=str(e))
            return 0

    # ==================== Health Check ====================

    async def ping(self) -> bool:
        """
        Ping Redis server.

        Returns:
            True if server responds
        """
        try:
            client = await self._get_client()
            return await client.ping()
        except Exception as e:
            logger.error("redis_ping_error", error=str(e))
            return False

    async def __aenter__(self):
        """Async context manager entry"""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
