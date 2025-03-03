from src.settings.components import PROJECT_PATH
from decouple import config


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': PROJECT_PATH + '\\db.sqlite3',
#     },
#     # 'settings_db': {
#     #     'ENGINE': 'django.db.backends.sqlite3',
#     #     'NAME': PROJECT_PATH + '\\configurations\\settings_db.sqlite3',
#     # }
# }

DATABASE_URL = config("DATABASE_URL", default="", cast=str)
# DATABASE_URL = "postgresql://postgres:postgres@192.168.1.8:5432/binando"

if DATABASE_URL != "":

    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=300,
            engine='timescale.db.backends.postgresql',
        )
    }
