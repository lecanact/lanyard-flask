from flask import Flask, request
from flask_socketio import SocketIO
from app.config import config_by_env
import time

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25
)

def create_app(env='development'):
    app = Flask(__name__)
    app.config.from_object(config_by_env(env))

    socketio.init_app(app)

    from app.api.v1 import v1_bp
    from app.api import discord_bp, metrics_bp
    from services import socketio_handler

    app.register_blueprint(v1_bp)
    app.register_blueprint(discord_bp)
    app.register_blueprint(metrics_bp)

    @app.before_request
    def before_request():
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        from services.metrics import inc_2xx, inc_4xx, inc_5xx, record_request_time

        duration = time.time() - request.start_time
        record_request_time(duration)

        if 200 <= response.status_code < 300:
            inc_2xx()
        elif 400 <= response.status_code < 500:
            inc_4xx()
        elif response.status_code >= 500:
            inc_5xx()

        return response

    @app.route('/')
    def index():
        from services.presence import get_monitored_users_count
        from services.metrics import set_monitored_users

        count = get_monitored_users_count()
        set_monitored_users(count)

        return {
            'info': 'Lanyard provides Discord presences as an API and WebSocket. Find out more here: https://github.com/Phineas/lanyard',
            'monitored_user_count': count,
            'discord_invite': 'https://discord.gg/lanyard'
        }, 200

    @app.errorhandler(404)
    def not_found(error):
        return {
            'error': {
                'code': 'not_found',
                'message': 'Route does not exist'
            },
            'success': False
        }, 404

    return app
