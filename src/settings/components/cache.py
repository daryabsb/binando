#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: Arvin
# datetime: 1/7/2021 3:54 PM
# software: BioTime
from src.settings.components.env import config

CACHE_HOST = config('CACHE_HOST', default='127.0.0.1')
CACHE_PORT = config('CACHE_PORT', default=6379)
CACHE_PASSWORD = config('CACHE_PASSWORD', default='')
CACHE_DB = config('CACHE_DB', default=1)

