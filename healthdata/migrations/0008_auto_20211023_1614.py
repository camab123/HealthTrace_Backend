# Generated by Django 3.2.8 on 2021-10-23 16:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0007_alter_manafacturer_manafacturerid'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Manafacturer',
            new_name='Manufacturer',
        ),
        migrations.RenameField(
            model_name='manufacturer',
            old_name='ManafacturerId',
            new_name='ManufacturerId',
        ),
    ]
