# Generated by Django 5.0.2 on 2024-02-24 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_alter_employee_has_notifications_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='point',
            name='working_hours',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Время работы'),
        ),
    ]
