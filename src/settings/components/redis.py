from decouple import config

# REDIS_URL = config("REDIS_URL", default='redis://localhost:6379')

REDIS_HOST = config("REDIS_HOST", default='192.168.1.8')
REDIS_PORT = config("REDIS_PORT", default=6378)

REDIS_URL = f'redis://{REDIS_HOST}:{str(REDIS_PORT)}'

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = "django-db"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"


CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_REDIS_BACKEND_USE_SSL = False
CELERY_BROKER_USE_SSL = False

REDIS_URL = config("REDIS_URL", default='redis://localhost:6379')

WSGI_APPLICATION = 'src.wsgi.application'
ASGI_APPLICATION = 'src.asgi.application'

# REDIS_URL = config("REDIS_URL", default='redis://localhost:6379')
# 172.16.10.8:6379
REDIS_HOST = config("REDIS_HOST", default='localhost')
REDIS_PORT = config("REDIS_PORT", default=6378)

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, REDIS_PORT)],  # Redis server
        },
    },
}
