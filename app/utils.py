import discord
from typing import Dict, Any

def activity_to_dict(activity: discord.Activity) -> Dict[str, Any]:
    """Convert Discord activity to dictionary."""
    data = {
        "type": activity.type.value,
        "name": activity.name,
        "id": getattr(activity, 'id', ''),
        "created_at": int(activity.created_at.timestamp() * 1000) if activity.created_at else None,
    }

    if activity.details:
        data["details"] = activity.details
    if activity.state:
        data["state"] = activity.state

    if hasattr(activity, 'timestamps') and activity.timestamps:
        data["timestamps"] = {
            "start": activity.timestamps.get("start"),
            "end": activity.timestamps.get("end"),
        }

    if hasattr(activity, 'assets') and activity.assets:
        data["assets"] = {
            "large_image": activity.assets.get("large_image", ""),
            "large_text": activity.assets.get("large_text", ""),
            "small_image": activity.assets.get("small_image", ""),
            "small_text": activity.assets.get("small_text", ""),
        }

    if hasattr(activity, 'sync_id'):
        data["sync_id"] = activity.sync_id

    return data
