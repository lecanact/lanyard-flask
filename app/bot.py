import logging, asyncio, discord
from discord.ext import commands
from services.redis_client import redis_client
from app.config import Config
from app.utils import activity_to_dict

logger = logging.getLogger(__name__)

class LanyardBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.presences = True
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(*args, intents=intents, **kwargs)

    async def on_ready(self):
        from services.presence import get_monitored_users_count
        logger.info(f"Bot logged in as {self.user}")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"Watching {get_monitored_users_count()} users | .apikey in DMs for a lanyard API key"
            )
        )

    async def on_presence_update(self, before, after):
        """Handle presence updates from Discord."""
        try:
            from services.socketio_handler import broadcast_presence_update

            user_id = str(after.id)
            presence_data = self._build_presence_data(after)
            broadcast_presence_update(user_id, presence_data)

        except Exception as e:
            logger.error(f"Error handling presence update: {e}")

    async def on_member_update(self, before, after):
        """Handle member updates (avatar changes, etc.)."""
        await self.on_presence_update(before, after)

    async def _fetch_user_profile(self, user_id: int) -> dict:
        """Fetch full user profile from Discord API using user token."""
        from app.config import Config
        user_token = Config.USER_TOKEN

        if not user_token:
            return {}

        try:
            async with self.http._session.get(
                f"https://discord.com/api/v10/users/{user_id}/profile",
                headers={"Authorization": user_token}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch user profile: {e}")
        return {}

    def get_user_presence(self, user_id: int) -> dict:
        """Get presence data for a user from Discord."""
        user = self.get_user(user_id)
        if not user:
            return None

        member = None
        for guild in self.guilds:
            member = guild.get_member(user_id)
            if member:
                break

        if member:
            return self._build_presence_data(member)
        else:
            return self._build_presence_data(user)
        
    def check_device(self, user, stat) -> str:
        """Check which device the user is active on."""
        
        if str(stat) == str(user.desktop_status):
            device = "Desktop"
        elif str(stat) == str(user.mobile_status):
            device = "Mobile"
        elif str(stat) == str(user.web_status):
            device = "Browser"
        else:
            device = "Unknown"
        return device


    def _build_presence_data(self, user) -> dict:
        """Build presence data from a Discord user."""
        import time
        user_id = str(user.id)
        
        extra_user_data = asyncio.run(self._fetch_user_profile(user.id))
        if extra_user_data:
            user = discord.Object(id=user.id, **extra_user_data)

        activities = []
        status = "offline"
        
        if hasattr(user, 'status'):
            status = str(user.status.value)

        if hasattr(user, 'activities'):
            for act in user.activities:
                activity_data = {
                    "type": act.type.value if hasattr(act, 'type') else 0,
                    "name": act.name if hasattr(act, 'name') else "",
                    "id": getattr(act, 'id', ''),
                    "created_at": act.created_at if hasattr(act, 'created_at') else None,
                    "session_id": getattr(act, 'session_id', ''),
                    "content_classification": {
                        "data": None,
                        "loaded": True
                    }
                }

                if hasattr(act, 'details') and act.details:
                    activity_data["details"] = act.details
                if hasattr(act, 'state') and act.state:
                    activity_data["state"] = act.state
                if hasattr(act, 'timestamps') and act.timestamps:
                    activity_data["timestamps"] = {
                        "start": act.timestamps.get("start"),
                        "end": act.timestamps.get("end"),
                    }
                if hasattr(act, 'assets') and act.assets:
                    activity_data["assets"] = {
                        "large_image": act.assets.get("large_image", ""),
                        "large_text": act.assets.get("large_text", ""),
                        "small_image": act.assets.get("small_image", ""),
                        "small_text": act.assets.get("small_text", ""),
                    }
                if hasattr(act, 'sync_id') and act.sync_id:
                    activity_data["sync_id"] = act.sync_id
                if hasattr(act, 'party') and act.party:
                    activity_data["party"] = act.party
                if hasattr(act, 'flags'):
                    activity_data["flags"] = act.flags
                if hasattr(act, 'application_id') and act.application_id:
                    activity_data["application_id"] = str(act.application_id)

                activities.append(activity_data)


        discord_user = {
            "username": user.name,
            "id": user_id,
            "avatar": user.avatar.key if user.avatar else None,
            "discriminator": user.discriminator or "0",
            "bot": user.bot if hasattr(user, 'bot') else False,
            "public_flags": user.public_flags.value if hasattr(user, 'public_flags') and user.public_flags else 0,
        }

        if hasattr(user, 'global_name'):
            discord_user["global_name"] = user.global_name
            
        dv = self.check_device(user, status)
        print(status)

        presence_data = {
            "user_id": user_id,
            "discord_user": discord_user,
            "discord_status": status,
            "active_on_discord_web": True if dv and "Browser" in dv else False,
            "active_on_discord_desktop": True if dv and "Desktop" in dv else False,
            "active_on_discord_mobile": True if dv and "Mobile" in dv else False,
            "active_on_discord_embedded": True if dv and "Embedded" in dv else False,
            "active_on_discord_vr": True if dv and "VR" in dv else False,
            "activities": activities,
        }
        print(dv)
        return presence_data

    async def setup_hook(self):
        """Load bot commands."""
        await self.add_cog(BotCommands(self))

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='apikey')
    async def apikey(self, ctx):
        """Generate or retrieve API key."""
        user_id = str(ctx.author.id)
        key = redis_client.get(f"user_api_key:{user_id}")

        if not key:
            import secrets
            key = secrets.token_urlsafe(32)
            redis_client.set(f"user_api_key:{user_id}", key)
            redis_client.set(f"api_key:{key}", user_id, ex=2592000)
            
        # create a DM object and send the API key there instead of the channel
        await ctx.author.send(f"Your API key is: `{key}`\nKeep this secret! It can be used to access your presence data.")
        
    @commands.command(name='set')
    async def set_kv(self, ctx, key: str, *, value: str):
        """Set a key-value pair."""
        from services.kv_store import set as kv_set

        user_id = str(ctx.author.id)
        success, error = kv_set(user_id, key, value)

        if success:
            await ctx.message.add_reaction('✅')
        else:
            await ctx.send(f"Error: {error}")

    @commands.command(name='get')
    async def get_kv(self, ctx, key: str):
        """Get a key-value pair."""
        from services.kv_store import get as kv_get

        user_id = str(ctx.author.id)
        value, error = kv_get(user_id, key)

        if value:
            await ctx.send(f"`{key}`: {value}")
        else:
            await ctx.send(f"Error: {error}")

    @commands.command(name='del')
    async def delete_kv(self, ctx, key: str):
        """Delete a key-value pair."""
        from services.kv_store import delete as kv_delete

        user_id = str(ctx.author.id)
        success, error = kv_delete(user_id, key)

        if success:
            await ctx.message.add_reaction('✅')
        else:
            await ctx.send(f"Error: {error}")

_bot_instance = None

def create_bot():
    """Create and return the Discord bot instance."""
    global _bot_instance
    _bot_instance = LanyardBot(command_prefix='.')
    return _bot_instance

def get_bot():
    """Get the running bot instance."""
    return _bot_instance
