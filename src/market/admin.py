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
    Company, CryptoCurency, Symbol, Order, Notification,
    CryptoCategory, Kline
)

admin.site.register(Company)
admin.site.register(CryptoCurency)
admin.site.register(Order)
admin.site.register(Notification)


@admin.register(CryptoCategory)
class CryptoCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'rank')
    ordering = ('rank', 'name')


count = 0


class SymbolAdmin(admin.ModelAdmin):
    list_display = ['rank', 'ticker', 'pair', 'get_24_hour_volume',
                    'active', 'enabled', 'timestamp', 'updated']
    list_filter = [
        'ticker',
        ('timestamp', DateTimeRangeFilterBuilder()),
        'timestamp',
        'active',
        'pair',
        'enabled',
    ]

    @staticmethod
    def initial_data():
        print('Initial called')
        global count
        print('Initial called')

        json_path = os.path.join(
            settings.BASE_DIR, 'market', 'coins.json')

        if not os.path.exists(json_path):
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            coins = json.load(f)

        for coin_data in coins:
            symbol = Symbol.objects.filter(ticker=coin_data['ticker']).first()

            if symbol:
                if symbol.coin == coin_data['coin'] or symbol.rank == coin_data['rank']:
                    continue

            if not symbol:
                # Create new symbol
                symbol = Symbol(
                    coin=coin_data['coin'],
                    ticker=coin_data['ticker'],
                    pair=f'{coin_data["ticker"]}USDT',
                    rank=coin_data['rank'],
                    price=coin_data['price'],
                    change_24h=coin_data['change_24h'],
                    market_cap=coin_data['market_cap'],
                    volume_24h=coin_data['volume24h'],
                    circ_supply=coin_data['circ_supply'],
                    logo=coin_data['logo'],
                )
                symbol.save(force_insert=True)
                count += 1
                print(count)
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
        # return qs.annotate(last_24_volume=Subquery(kline_subquery))
        queryset = qs.annotate(last_24_volume=Subquery(kline_subquery))
        return queryset


class KlineAdmin(admin.ModelAdmin):
    list_display = ['id', 'symbol', 'close', 'localized_time', 'time']
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
