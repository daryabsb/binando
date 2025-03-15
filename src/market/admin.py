import zoneinfo
import os
import json
from django.conf import settings
from django.contrib import admin
from django.utils import timezone
from tzlocal import get_localzone
from django.utils.text import slugify
from rangefilter.filters import (
    DateTimeRangeFilterBuilder,
)
from django.db.models import OuterRef, Subquery
from src.market.models import (
    Company, CryptoCurency, Kline, Symbol, Order, Notification,
    CryptoCategory
)

admin.site.register(Company)
admin.site.register(CryptoCurency)
admin.site.register(Order)
admin.site.register(Notification)


@admin.register(CryptoCategory)
class CryptoCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'rank')
    ordering = ('rank', 'name')


class SymbolAdmin(admin.ModelAdmin):
    list_display = ['ticker', 'pair', 'get_24_hour_volume',
                    'active', 'timestamp', 'updated']
    list_filter = [
        'ticker',
        ('timestamp', DateTimeRangeFilterBuilder()),
        'timestamp'
    ]

    @staticmethod
    def initial_data():
        print('Initial called')

        json_path = os.path.join(
            settings.BASE_DIR, 'src', 'market', 'coins.json')
        print('path = ', json_path)

        if not os.path.exists(json_path):
            return

        with open(json_path, 'r') as f:
            coins = json.load(f)

        for coin_data in coins:
            symbol = Symbol.objects.filter(ticker=coin_data['ticker']).first()
            if not symbol:
                # Create new symbol
                symbol = Symbol(
                    coin=coin_data['coin'],
                    ticker=coin_data['ticker'],
                    rank=coin_data['rank'],
                    price=coin_data['price'],
                    change_24h=coin_data['change_24h'],
                    market_cap=coin_data['market_cap'],
                    volume_24h=coin_data['volume24h'],
                    circ_supply=coin_data['circ_supply'],
                    logo=coin_data['logo'],
                )
                symbol.save(force_insert=True)
            else:
                # Update existing symbol
                symbol.coin = coin_data['coin']
                symbol.rank = coin_data['rank']
                symbol.price = coin_data['price']
                symbol.change_24h = coin_data['change_24h']
                symbol.market_cap = coin_data['market_cap']
                symbol.volume_24h = coin_data['volume24h']
                symbol.circ_supply = coin_data['circ_supply']
                symbol.logo = coin_data['logo']
                symbol.save(force_update=True)

            # Handle categories
            category_names = coin_data['category'].split(', ')
            for cat_name in category_names:
                category, _ = CryptoCategory.objects.get_or_create(
                    name=cat_name,
                    defaults={'slug': slugify(cat_name), 'rank': symbol.rank}
                )
                symbol.categories.add(category)

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
