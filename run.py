#!/usr/bin/env python3
import os
import logging
import threading
from app import create_app, socketio
from app.bot import create_bot
from services.redis_client import redis_client
from app.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

redis_client.connect(
    host=app.config['REDIS_HOST'],
    port=app.config['REDIS_PORT'],
    db=app.config['REDIS_DB'],
    password=app.config['REDIS_PASSWORD']
)

@app.shell_context_processor
def make_shell_context():
    return {'app': app, 'redis_client': redis_client}

def run_bot():
    """Run the Discord bot in a separate thread."""
    bot = create_bot()
    bot.run(app.config['BOT_TOKEN'])

if __name__ == '__main__':
    if app.config['BOT_TOKEN']:
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("Discord bot started in background thread")

    port = app.config['HTTP_PORT']
    logger.info(f"Starting Lanyard on port {port}...")
    socketio.run(app, host='0.0.0.0', port=port, debug=app.debug)

