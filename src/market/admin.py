import zoneinfo
from django.contrib import admin
from django.utils import timezone
from tzlocal import get_localzone
from rangefilter.filters import (
    DateTimeRangeFilterBuilder,
)
from django.db.models import OuterRef, Subquery
from .models import Company, CryptoCurency, Kline, Symbol, Order, Notification

admin.site.register(Company)
admin.site.register(CryptoCurency)
admin.site.register(Order)
admin.site.register(Notification)


class SymbolAdmin(admin.ModelAdmin):
    list_display = ['ticker', 'pair', 'get_24_hour_volume',
                    'active', 'timestamp', 'updated']
    list_filter = [
        'ticker',
        ('timestamp', DateTimeRangeFilterBuilder()),
        'timestamp'
    ]

    def get_24_hour_volume(self, obj):
        from src.market.models import Kline
        last_24_hours = timezone.now() - timezone.timedelta(hours=24)
        kline = Kline.objects.filter(
            symbol=obj.pair,
            time__gte=last_24_hours
        ).last()

        return f"{kline.volume:.4f}" if kline else "0.0000"
    get_24_hour_volume.short_description = "(24h) Volume"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        last_24_hours = timezone.now() - timezone.timedelta(hours=24)
        kline_subquery = Kline.objects.filter(
            symbol=OuterRef('pair'),
            time__gte=last_24_hours
        ).order_by('time').values('volume')[:1]
        return qs.annotate(last_24_volume=Subquery(kline_subquery))


class KlineAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'close', 'localized_time', 'time']
    list_filter = [
        'symbol',
        ('time', DateTimeRangeFilterBuilder()),
        'time'
    ]

    readonly_fields = ['localized_time', 'time']

    def localized_time(self, obj):
        # Convert the stored datetime to UTC first.
        from datetime import timezone
        utc_time = obj.time.astimezone(timezone.utc)
        # Then convert from UTC to your system's local timezone.
        tz_name = str(get_localzone())
        user_tz = zoneinfo.ZoneInfo(tz_name)
        local_time = utc_time.astimezone(timezone.utc)
        return local_time.strftime("%b %d, %Y, %I:%M %p (%Z)")

    def get_queryset(self, request):
        tz_name = "US/Eastern"
        # tz_name = "UTC"
        user_tz = zoneinfo.ZoneInfo(tz_name)
        timezone.activate(user_tz)
        return super().get_queryset(request).order_by('-time')


admin.site.register(Kline, KlineAdmin)
admin.site.register(Symbol, SymbolAdmin)
