# Generated by Django 5.0.2 on 2024-02-14 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_orderitem'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='orderitem',
            unique_together={('order', 'product')},
        ),
    ]
