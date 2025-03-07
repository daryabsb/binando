# Generated by Django 5.1.6 on 2025-03-04 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CryptoCurency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('ticker', models.CharField(db_index=True, max_length=20, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('balance', models.DecimalField(decimal_places=17, max_digits=20)),
                ('pnl', models.DecimalField(decimal_places=17, default=0, max_digits=20)),
                ('active', models.BooleanField(default=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
