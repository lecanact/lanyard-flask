import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

    BOT_TOKEN = os.getenv('BOT_TOKEN')
    USER_TOKEN = os.getenv('USER_TOKEN')
    BOT_IDEMPOTENCY_ENV_KEY = os.getenv('BOT_IDEMPOTENCY_ENV_KEY')

    HTTP_PORT = int(os.getenv('HTTP_PORT', 4001))

    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    REDIS_DB = 15

def config_by_env(env='development'):
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    return config_map.get(env, DevelopmentConfig)
