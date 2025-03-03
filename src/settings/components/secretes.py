from src.settings.components.env import config
# from src.settings.components.config_file import CONFIG_FILE

SITE_ID = 1

SECRET_KEY = config("SECRET_KEY", default=None)
DEBUG = config('DJANGO_DEBUG', default=1)

try:
    DEBUG = int(DEBUG)
except ValueError:
    if DEBUG == 'true':
        DEBUG = 1
    else:
        DEBUG = 0

ALLOWED_HOSTS = ['172.16.10.49']
ALLOWED_HOST = config("ALLOWED_HOST", cast=str, default="")

if ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(ALLOWED_HOST.strip())
