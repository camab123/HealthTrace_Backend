# Generated by Django 3.2.8 on 2021-10-31 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0023_auto_20211031_1859'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['Doctor'], name='healthdata__Doctor__8c53ab_idx'),
        ),
    ]
