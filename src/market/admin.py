import zoneinfo
from django.contrib import admin
from django.utils import timezone
from rangefilter.filters import (
    DateTimeRangeFilterBuilder,
)
from .models import Company, CryptoCurency

admin.site.register(Company)
admin.site.register(CryptoCurency)
