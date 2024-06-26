# Generated by Django 4.2.13 on 2024-06-30 21:07

from django.db import migrations


def create_defaults_for_users(apps, schema_editor):
    TwitchUser = apps.get_model('accounts', 'TwitchUser')
    SongReqOverlay = apps.get_model('overlay', 'SongReqOverlay')
    
    for user in TwitchUser.objects.all():
        SongReqOverlay.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('overlay', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_defaults_for_users),
    ]
