# Generated by Django 3.2.8 on 2021-10-27 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0017_transactionitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='transactionitems',
            field=models.ManyToManyField(to='healthdata.TransactionItem'),
        ),
    ]