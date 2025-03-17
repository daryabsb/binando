from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task
def test_tasks():
    print('test_works')
    return 'Bravo!!'

@shared_task
def update_usd_value():
    from src.market.utils import get_total_usd
    total_usd = get_total_usd()

    group_name = 'total_usd_update'
    message_type = 'total_usd'

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': message_type,
            'data': str(total_usd),  # Convert datetime to string
        }
    )