# Generated by Django 4.2.2 on 2024-05-06 02:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('functions', '0004_alter_commandfunction_function'),
    ]

    operations = [
        migrations.RenameField(
            model_name='commandfunction',
            old_name='function',
            new_name='binded_to',
        ),
    ]
