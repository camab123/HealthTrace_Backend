# Generated by Django 3.2.9 on 2021-11-27 19:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0045_createstatetable'),
    ]

    operations = [
        migrations.DeleteModel(
            name='State',
        ),
    ]