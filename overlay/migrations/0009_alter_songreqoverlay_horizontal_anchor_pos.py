# Generated by Django 4.2.13 on 2024-07-01 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('overlay', '0008_alter_ytreqoverlay_height_alter_ytreqoverlay_width'),
    ]

    operations = [
        migrations.AlterField(
            model_name='songreqoverlay',
            name='horizontal_anchor_pos',
            field=models.CharField(default='left', max_length=12),
        ),
    ]
