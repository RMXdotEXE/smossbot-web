# Generated by Django 4.2.13 on 2024-07-01 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('overlay', '0003_songreqoverlay_background'),
    ]

    operations = [
        migrations.AddField(
            model_name='songreqoverlay',
            name='constant',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='songreqoverlay',
            name='enabled',
            field=models.BooleanField(default=False),
        ),
    ]
