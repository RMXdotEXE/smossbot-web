# Generated by Django 4.2.2 on 2024-05-06 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('functions', '0002_rename_functioncommand_commandfunction'),
    ]

    operations = [
        migrations.AddField(
            model_name='commandfunction',
            name='has_cooldown',
            field=models.BooleanField(default=True),
        ),
    ]