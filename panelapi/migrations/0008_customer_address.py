# Generated by Django 4.2.5 on 2024-12-06 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panelapi', '0007_order_total_after_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
    ]
