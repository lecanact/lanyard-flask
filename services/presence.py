import json
import logging
from typing import Dict, Any, Optional
from services.redis_client import redis_client

logger = logging.getLogger(__name__)

DISCORD_SPOTIFY_ACTIVITY_ID = "spotify:1"

def get_monitored_users_count() -> int:
    """Get count of monitored users."""
    return redis_client.scard("lanyard:monitored_users")

def get_pretty_presence(user_id: str) -> tuple[int, Dict[str, Any]]:
    """Get formatted presence data for a user."""
    presence_key = f"lanyard_presence:{user_id}"
    kv_key = f"lanyard_kv:{user_id}"

    presence_data = redis_client.get(presence_key)
    if not presence_data:
        return 404, {"error": "User not found", "success": False}

    try:
        presence = json.loads(presence_data)
    except json.JSONDecodeError:
        return 500, {"error": "Invalid presence data", "success": False}

    kv_data = redis_client.hgetall(kv_key) or {}

    pretty = build_pretty_presence(presence, kv_data)
    return 200, {"success": True, "data": pretty}

def build_pretty_presence(presence: Dict[str, Any], kv_data: Dict[str, str]) -> Dict[str, Any]:
    """Build a pretty presence object from raw presence data and KV."""
    discord_status = presence.get("status", "offline")
    activities = presence.get("activities", [])
    discord_user = presence.get("discord_user", {})

    pretty = {
        "discord_user": discord_user,
        "discord_status": discord_status,
        "active_on_discord_web": presence.get("active_on_discord_web", False),
        "active_on_discord_desktop": presence.get("active_on_discord_desktop", False),
        "active_on_discord_mobile": presence.get("active_on_discord_mobile", False),
        "active_on_discord_embedded": presence.get("active_on_discord_embedded", False),
        "active_on_discord_vr": presence.get("active_on_discord_vr", False),
        "listening_to_spotify": False,
        "spotify": None,
        "activities": activities,
        "kv": kv_data
    }

    for activity in activities:
        if activity.get("id") == DISCORD_SPOTIFY_ACTIVITY_ID:
            pretty["listening_to_spotify"] = True
            pretty["spotify"] = extract_spotify_data(activity)
            break

    return pretty

def extract_spotify_data(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Extract Spotify-specific data from activity."""
    assets = activity.get("assets", {})
    timestamps = activity.get("timestamps", {})

    return {
        "track_id": activity.get("sync_id", ""),
        "timestamps": timestamps,
        "song": activity.get("details", ""),
        "artist": activity.get("state", ""),
        "album_art_url": f"https://i.scdn.co/image/{assets.get('large_image', '').replace('spotify:', '')}",
        "album": activity.get("assets", {}).get("large_text", ""),
    }

def update_presence(user_id: str, presence_data: Dict[str, Any]):
    """Update user presence in cache and broadcast to subscribers."""
    presence_key = f"lanyard_presence:{user_id}"
    redis_client.set(presence_key, json.dumps(presence_data))
    redis_client.sadd("lanyard:monitored_users", user_id)

    from services.socketio_handler import broadcast_presence_update
    broadcast_presence_update(user_id, presence_data)

def remove_presence(user_id: str):
    """Remove user from monitored users."""
    presence_key = f"lanyard_presence:{user_id}"
    redis_client.delete(presence_key)
    redis_client.srem("lanyard:monitored_users", user_id)

def subscribe_to_ids_and_build(user_ids: list) -> Dict[str, Any]:
    """Build init state for multiple user subscriptions."""
    result = {}
    for user_id in user_ids:
        status, data = get_pretty_presence(user_id)
        if status == 200:
            result[user_id] = data["data"]
    return result

def get_all_kv(user_id: str) -> Dict[str, str]:
    """Get all KV pairs for a user."""
    from services.kv_store import get_all
    return get_all(user_id)

