# Generated by Django 5.0.2 on 2024-02-09 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_owner_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='is_active',
            field=models.BooleanField(default=False, verbose_name='Активный'),
        ),
    ]
