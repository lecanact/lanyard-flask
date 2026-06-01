import discord
from discord.ext import commands
import logging
import json
from services.redis_client import redis_client
from services.presence import update_presence, remove_presence
from app.config import Config
from app.utils import activity_to_dict

logger = logging.getLogger(__name__)

class LanyardBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.guilds = True

        super().__init__(*args, intents=intents, **kwargs)

    async def on_ready(self):
        logger.info(f"Bot logged in as {self.user}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"presences | /help"
            )
        )

    async def on_presence_update(self, before, after):
        """Handle presence updates from Discord."""
        try:
            user_id = str(after.user.id)

            presence_data = {
                "user_id": user_id,
                "discord_user": {
                    "username": after.user.name,
                    "id": user_id,
                    "avatar": after.user.avatar.key if after.user.avatar else None,
                    "discriminator": after.user.discriminator or "0",
                },
                "status": str(after.status),
                "active_on_discord_web": after.web_status == discord.Status.online,
                "active_on_discord_desktop": after.desktop_status == discord.Status.online,
                "active_on_discord_mobile": after.mobile_status == discord.Status.online,
                "activities": [activity_to_dict(act) for act in after.activities],
            }

            update_presence(user_id, presence_data)

            redis_client.publish(
                "lanyard:global_sync",
                json.dumps({
                    "user_id": user_id,
                    "diff": presence_data
                })
            )

        except Exception as e:
            logger.error(f"Error handling presence update: {e}")

    async def on_member_update(self, before, after):
        """Handle member updates (avatar changes, etc.)."""
        await self.on_presence_update(before, after)

    async def setup_hook(self):
        """Load bot commands."""
        await self.load_cog(BotCommands(self))

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

        await ctx.author.send(f"Your API key: `{key}`")
        await ctx.message.delete()

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

def create_bot():
    """Create and return the Discord bot instance."""
    bot = LanyardBot(command_prefix='.')
    return bot
