# Generated by Django 3.2.8 on 2021-10-22 20:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('DoctorId', models.IntegerField(primary_key=True, serialize=False)),
                ('FirstName', models.CharField(max_length=30)),
                ('MiddleName', models.CharField(max_length=30)),
                ('LastName', models.CharField(max_length=35)),
                ('PrimaryType', models.CharField(max_length=40)),
                ('Specialty', models.CharField(max_length=30)),
                ('StreetAddress1', models.CharField(max_length=50)),
                ('StreetAddress2', models.CharField(max_length=50)),
                ('City', models.CharField(max_length=30)),
                ('State', models.CharField(max_length=20)),
                ('ZipCode', models.CharField(max_length=15)),
                ('Country', models.CharField(max_length=30)),
            ],
            options={
                'ordering': ['FirstName', 'LastName'],
            },
        ),
        migrations.CreateModel(
            name='Manafacturer',
            fields=[
                ('ManafacturerId', models.IntegerField(primary_key=True, serialize=False)),
                ('Name', models.CharField(max_length=100)),
                ('State', models.CharField(max_length=100)),
                ('Country', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['Name'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('TransactionId', models.IntegerField(primary_key=True, serialize=False)),
                ('Type_Product', models.CharField(max_length=100)),
                ('Category', models.CharField(max_length=100)),
                ('Name', models.CharField(max_length=100)),
                ('Pay_Amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('Date', models.DateField()),
                ('Payment', models.CharField(max_length=100)),
                ('Nature_Payment', models.CharField(max_length=100)),
                ('Contextual_Info', models.CharField(max_length=100)),
                ('Doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='healthdata.doctor')),
                ('Manafacturer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='healthdata.manafacturer')),
            ],
            options={
                'ordering': ['Date', 'Name'],
            },
        ),
    ]
