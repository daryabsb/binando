from django.apps import AppConfig


class MarketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.market'
    
    # def ready(self):
    #     from django.conf import settings
    #     # Only trigger the stream task in DEBUG mode
    #     if settings.DEBUG:
    #         from src.market.tasks import stream_kline_data, fill_kline_gaps
    #         gaps_filled = fill_kline_gaps()
    #         if gaps_filled:
    #             stream_kline_data.delay()  # Start the task asynchronously