# Generated by Django 3.2.8 on 2021-10-26 21:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('healthdata', '0015_auto_20211026_2031'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['-Date']},
        ),
        migrations.AlterField(
            model_name='transaction',
            name='Doctor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='healthdata.doctor'),
        ),
    ]
