# Generated by Django 3.2.8 on 2021-10-22 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0003_auto_20211022_2041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctor',
            name='Specialty',
            field=models.CharField(max_length=300, null=True),
        ),
    ]