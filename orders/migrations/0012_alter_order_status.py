# Generated by Django 5.0.2 on 2024-03-14 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_alter_specialprice_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('CR', 'Создан'), ('AC', 'Принят')], default='CR', max_length=32, verbose_name='Статус'),
        ),
    ]
