# Generated by Django 5.0.6 on 2024-10-20 15:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0004_rename_wake_time_sleepinglog_wake_up_time_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sleepinglog",
            name="sleep_date",
        ),
        migrations.RemoveField(
            model_name="sleepinglog",
            name="wake_up_date",
        ),
    ]
