# Generated by Django 4.2.5 on 2024-12-02 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panelapi', '0004_customer_outlet'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='mode_of_payment',
            field=models.CharField(choices=[('CASH', 'Cash'), ('CARD', 'Card'), ('UPI', 'UPI'), ('ONLINE', 'Online Payment'), ('OTHER', 'Other')], default='CASH', max_length=20),
        ),
    ]
