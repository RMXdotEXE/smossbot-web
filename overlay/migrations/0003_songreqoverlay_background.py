# Generated by Django 4.2.13 on 2024-07-01 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('overlay', '0002_add_default_songreqoverlay_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='songreqoverlay',
            name='background',
            field=models.BooleanField(default=False),
        ),
    ]
