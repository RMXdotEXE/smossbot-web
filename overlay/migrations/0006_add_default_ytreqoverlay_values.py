# Generated by Django 4.2.13 on 2024-07-01 15:07

from django.db import migrations


def create_defaults_for_users(apps, schema_editor):
    TwitchUser = apps.get_model('accounts', 'TwitchUser')
    YTReqOverlay = apps.get_model('overlay', 'YTReqOverlay')
    
    for user in TwitchUser.objects.all():
        YTReqOverlay.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('overlay', '0005_ytreqoverlay'),
    ]

    operations = [
        migrations.RunPython(create_defaults_for_users),
    ]
