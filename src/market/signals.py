
from django.dispatch import receiver
from src.market.models import Order, CryptoCurency

# @receiver(post_save, sender=CryptoCurency)
# def notify_on_save(sender, instance, created, **kwargs):
#     # if created:
#     instance.send_event()


@receiver(post_save, sender=Order)
def notify_on_save(sender, instance, created, **kwargs):
    if created:
        instance.send_event()
        crypto = instance.crypto
        # queryset = CryptoCurency.objects.all()
        cryptos = CryptoCurency.objects.get_cryptos_with_sparkline(
            kline_amount=25)
        crypto.send_queryset_data(cryptos)
        # crypto.send_event()

        # print(queryset.count())


@receiver(post_save, sender=CryptoCurency)
def update_usdt_on_save(sender, instance, created, **kwargs):
    if not created and instance.ticker == 'USDT':
        instance.update_usdt()
