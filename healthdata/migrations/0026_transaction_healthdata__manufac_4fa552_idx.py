# Generated by Django 3.2.8 on 2021-11-02 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0025_auto_20211102_2333'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['Manufacturer'], name='healthdata__Manufac_4fa552_idx'),
        ),
    ]
