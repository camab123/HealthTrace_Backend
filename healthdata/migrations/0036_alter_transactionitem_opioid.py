# Generated by Django 3.2.9 on 2021-11-13 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0035_rename_opiod_transactionitem_opioid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactionitem',
            name='Opioid',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]