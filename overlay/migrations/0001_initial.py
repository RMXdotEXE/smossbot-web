# Generated by Django 4.2.13 on 2024-06-30 20:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SongReqOverlay',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('horizontal_anchor_pos', models.CharField(default='left', max_length=12)),
                ('vertical_anchor_pos', models.CharField(default='top', max_length=12)),
            ],
        ),
    ]