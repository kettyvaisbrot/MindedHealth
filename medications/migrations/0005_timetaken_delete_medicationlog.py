# Generated by Django 5.0.6 on 2024-10-27 16:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("medications", "0004_alter_medication_times_per_day_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimeTaken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("time", models.TimeField()),
                (
                    "medication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="times_taken",
                        to="medications.medication",
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="MedicationLog",
        ),
    ]
