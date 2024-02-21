# Generated by Django 5.0.2 on 2024-02-21 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_alter_order_owner'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderAcceptance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('OP', 'Открыт'), ('CL', 'Закрыт')], default='OP', max_length=16, verbose_name='Статус')),
            ],
            options={
                'verbose_name': 'Прием заказов',
                'verbose_name_plural': 'Прием заказов',
            },
        ),
    ]