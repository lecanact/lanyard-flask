import logging
from typing import Dict, Tuple, Optional
from services.redis_client import redis_client

logger = logging.getLogger(__name__)

KV_MAX_VALUE_LENGTH = 30_000
KV_MAX_PAIRS_PER_USER = 512

def validate_pair(key: str, value: str) -> Tuple[bool, Optional[str]]:
    """Validate a KV pair."""
    if not key or not isinstance(key, str):
        return False, "Key must be a non-empty string"

    if not value or not isinstance(value, str):
        return False, "Value must be a non-empty string"

    if len(key) > 255:
        return False, "Key must be 255 characters or less"

    if not key.isalnum():
        return False, "Key must be alphanumeric (a-zA-Z0-9)"

    if len(value) > KV_MAX_VALUE_LENGTH:
        return False, f"Value must be {KV_MAX_VALUE_LENGTH} characters or less"

    return True, None

def set(user_id: str, key: str, value: str) -> Tuple[bool, Optional[str]]:
    """Set a KV pair for a user."""
    valid, error = validate_pair(key, value)
    if not valid:
        return False, error

    kv_key = f"lanyard_kv:{user_id}"

    current_pairs = redis_client.hgetall(kv_key)
    if len(current_pairs) >= KV_MAX_PAIRS_PER_USER and key not in current_pairs:
        return False, f"User can only have {KV_MAX_PAIRS_PER_USER} key-value pairs"

    redis_client.hset(kv_key, {key: value})
    return True, None

def get(user_id: str, key: str) -> Tuple[Optional[str], Optional[str]]:
    """Get a KV value for a user."""
    kv_key = f"lanyard_kv:{user_id}"
    value = redis_client.hget(kv_key, key)
    if value is None:
        return None, "Key not found"
    return value, None

def delete(user_id: str, key: str) -> Tuple[bool, Optional[str]]:
    """Delete a KV pair for a user."""
    kv_key = f"lanyard_kv:{user_id}"
    deleted = redis_client.hdel(kv_key, key)
    if deleted:
        return True, None
    return False, "Key not found"

def multiset(user_id: str, pairs: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """Set multiple KV pairs for a user."""
    kv_key = f"lanyard_kv:{user_id}"

    for key, value in pairs.items():
        valid, error = validate_pair(key, value)
        if not valid:
            return False, f"Invalid pair ({key}): {error}"

    current_pairs = redis_client.hgetall(kv_key)
    new_keys = set(pairs.keys()) - set(current_pairs.keys())

    if len(current_pairs) + len(new_keys) > KV_MAX_PAIRS_PER_USER:
        return False, f"User can only have {KV_MAX_PAIRS_PER_USER} key-value pairs"

    redis_client.hset(kv_key, pairs)
    return True, None

def get_all(user_id: str) -> Dict[str, str]:
    """Get all KV pairs for a user."""
    kv_key = f"lanyard_kv:{user_id}"
    return redis_client.hgetall(kv_key) or {}
