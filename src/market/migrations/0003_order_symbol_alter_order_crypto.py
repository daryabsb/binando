# Generated by Django 5.1.6 on 2025-03-26 12:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0002_kline_unique_kline'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='symbol',
            field=models.CharField(blank=True, max_length=35, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='crypto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='market.cryptocurency'),
        ),
    ]
