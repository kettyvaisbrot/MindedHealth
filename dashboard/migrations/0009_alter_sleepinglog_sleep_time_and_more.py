# Generated by Django 5.0.6 on 2024-10-25 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0008_alter_sleepinglog_unique_together"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sleepinglog",
            name="sleep_time",
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name="sleepinglog",
            name="wake_time",
            field=models.TimeField(),
        ),
    ]
