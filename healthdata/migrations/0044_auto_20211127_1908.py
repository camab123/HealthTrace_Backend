# Generated by Django 3.2.9 on 2021-11-27 19:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0043_auto_20211127_1904'),
    ]

    operations = [
        migrations.RenameField(
            model_name='state',
            old_name='MapData',
            new_name='map',
        ),
        migrations.RenameField(
            model_name='state',
            old_name='SummaryData',
            new_name='summary',
        ),
    ]
