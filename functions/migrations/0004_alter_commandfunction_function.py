# Generated by Django 4.2.2 on 2024-05-06 02:33

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('functions', '0003_commandfunction_has_cooldown'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commandfunction',
            name='function',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=20), default=list, size=None),
        ),
    ]
