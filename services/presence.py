import logging
from typing import Dict, Any, Optional
from services.kv_store import get_all as kv_get_all

logger = logging.getLogger(__name__)

DISCORD_SPOTIFY_ACTIVITY_ID = "spotify:1"

def get_monitored_users_count() -> int:
    """Get count of monitored users from Discord."""
    from app.bot import get_bot
    bot = get_bot()
    if not bot or not bot.user:
        return 0

    total_users = set()
    for guild in bot.guilds:
        for member in guild.members:
            total_users.add(member.id)
    return len(total_users)

def get_pretty_presence(user_id: str) -> tuple[int, Dict[str, Any]]:
    """Get formatted presence data for a user from Discord."""
    from app.bot import get_bot
    bot = get_bot()

    if not bot or not bot.user:
        return 503, {
            "error": {"code": "bot_unavailable", "message": "Discord bot is not ready"},
            "success": False
        }

    try:
        user_id_int = int(user_id)
    except ValueError:
        return 400, {
            "error": {"code": "invalid_user_id", "message": "Invalid user ID format"},
            "success": False
        }

    presence_data = bot.get_user_presence(user_id_int)
    if not presence_data:
        return 404, {
            "error": {
                "code": "user_not_monitored",
                "message": "User is not being monitored by Lanyard"
            },
            "success": False
        }

    kv_data = kv_get_all(user_id) or {}
    pretty = build_pretty_presence(presence_data, kv_data)
    return 200, {"success": True, "data": pretty}

def build_pretty_presence(presence: Dict[str, Any], kv_data: Dict[str, str]) -> Dict[str, Any]:
    """Build a pretty presence object from raw presence data and KV."""

    pretty = {
        "discord_user": presence.get("discord_user", "Unknown User"),
        "discord_status": presence.get("discord_status", "offline"),
        "active_on_discord_web": presence.get("active_on_discord_web", False),
        "active_on_discord_desktop": presence.get("active_on_discord_desktop", False),
        "active_on_discord_mobile": presence.get("active_on_discord_mobile", False),
        "active_on_discord_embedded": presence.get("active_on_discord_embedded", False),
        "active_on_discord_vr": presence.get("active_on_discord_vr", False),
        "listening_to_spotify": presence.get("listening_to_spotify", False),
        "spotify": presence.get("spotify", {}),
        "activities": presence.get("activities", {}),
        "kv": presence.get("kv", {}),
    }

    for activity in pretty["activities"]:
        if activity.get("name") == "Spotify" and activity.get("type") == 2:
            pretty["listening_to_spotify"] = True
            pretty["spotify"] = extract_spotify_data(activity)
            print(activity)
            break

    return pretty

def extract_spotify_data(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Extract Spotify-specific data from activity."""
    assets = activity.get("assets", {})
    timestamps = activity.get("timestamps", {})

    large_image = assets.get("large_image", "")
    album_art_url = ""
    if large_image:
        if large_image.startswith("spotify:"):
            album_art_url = f"https://i.scdn.co/image/{large_image.replace('spotify:', '')}"
        else:
            album_art_url = f"https://i.scdn.co/image/{large_image}"

    return {
        "track_id": activity.get("sync_id", ""),
        "timestamps": timestamps,
        "song": activity.get("details", ""),
        "artist": activity.get("state", ""),
        "album_art_url": album_art_url,
        "album": assets.get("large_text", ""),
    }

def subscribe_to_ids_and_build(user_ids: list) -> Dict[str, Any]:
    """Build init state for multiple user subscriptions."""
    result = {}
    for user_id in user_ids:
        status, data = get_pretty_presence(user_id)
        if status == 200:
            result[user_id] = data["data"]
    return result
