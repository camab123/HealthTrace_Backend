from django.db import models

# Create your models here.
class Doctor(models.Model):
    DoctorId = models.IntegerField(primary_key=True)
    FirstName = models.CharField(max_length=35, null=True)
    MiddleName = models.CharField(max_length=30, null=True)
    LastName = models.CharField(max_length=35, null=True)
    PrimaryType = models.CharField(max_length=100, null=True)
    Specialty = models.CharField(max_length=300, null=True)
    StreetAddress1 = models.CharField(max_length=80, null=True)
    StreetAddress2 = models.CharField(max_length=80, null=True)
    City = models.CharField(max_length=50, null=True)
    State = models.CharField(max_length=20, null=True)
    ZipCode = models.CharField(max_length=15, null=True)
    Country = models.CharField(max_length=100, null=True)

    class Meta:
        ordering = ['FirstName', 'MiddleName', 'LastName']

    def __str__(self):
        return str(self.FirstName) + " " + str(self.MiddleName) + " " + str(self.LastName)

    def serialize(self):
        return {
            'DoctorId': self.DoctorId,
            'FirstName': self.FirstName,
            'MiddleName': self.MiddleName,
            'LastName': self.LastName,
            'PrimaryType': self.PrimaryType,
            'Specialty': self.Specialty,
            'StreetAddress1': self.StreetAddress1,
            'StreetAddress2': self.StreetAddress2,
            'City': self.City,
            'State': self.State,
            'ZipCode': self.ZipCode,
            'Country': self.Country,
        }

class Manufacturer(models.Model):
    ManufacturerId = models.BigIntegerField(primary_key=True)
    Name = models.CharField(max_length=100, null=True)
    State = models.CharField(max_length=100, null=True)
    Country = models.CharField(max_length=100, null=True)
    class Meta:
        ordering = ['Name']
    
    def __str__(self):
        return str(self.Name)
    
    def serialize(self):
        return {
            'ManufacturerId': self.ManufacturerId,
            'Name': self.Name,
            'State': self.State,
            'Country': self.Country,
        }
    
class Transaction(models.Model):
    TransactionId = models.IntegerField(primary_key=True)
    Doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    Manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    Type_Product = models.CharField(max_length=100, null=True)
    Category = models.CharField(max_length=100, null=True)
    Name = models.CharField(max_length=100, null=True)
    Pay_Amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    Date = models.DateField(null=True)
    Payment = models.CharField(max_length=100, null=True)
    Nature_Payment = models.CharField(max_length=200, null=True)
    Contextual_Info = models.CharField(max_length=500, null=True)

    class Meta:
        ordering = ['Date', 'Name']
    
    def __str__(self):
        return "#{} on date {}".format(str(self.TransactionId), str(self.Date))
    
    def serialize(self):
        return {
            'TransactionId': self.TransactionId,
            'Doctor': self.Doctor.DoctorId,
            'Manufacturer': self.Manufacturer.Name,
            'Type_Product': self.Type_Product,
            'Category': self.Category,
            'Name': self.Name,
            'Pay_Amount': self.Pay_Amount,
            'Date': self.Date,
            'Payment': self.Payment,
            'Nature_Payment': self.Nature_Payment,
            'Contextual_Info': self.Contextual_Info,
        }
