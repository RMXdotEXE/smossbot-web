# Generated by Django 4.2.13 on 2024-07-01 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('overlay', '0007_ytreqoverlay_height_ytreqoverlay_width'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ytreqoverlay',
            name='height',
            field=models.IntegerField(default=480),
        ),
        migrations.AlterField(
            model_name='ytreqoverlay',
            name='width',
            field=models.IntegerField(default=854),
        ),
    ]
