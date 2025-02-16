from split_settings.tools import include
from os import environ


base_settings = [
    'components/paths.py',
    'components/db.py',
    'components/common.py',
    'components/secretes.py',
]

include(*base_settings)
