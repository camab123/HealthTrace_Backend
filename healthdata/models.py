from django.db import models
from django.db import connection
# Create your models here.
class Doctor(models.Model):
    DoctorId = models.IntegerField(primary_key=True)
    FirstName = models.CharField(max_length=35, null=True)
    MiddleName = models.CharField(max_length=30, null=True)
    LastName = models.CharField(max_length=35, null=True)
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

    def serialize_doc(self):
        return {
            "FirstName": self.FirstName,
            "MiddleName": self.MiddleName,
            "LastName": self.LastName,
            "Specialty": self.Specialty,
            "StreetAddress1": self.StreetAddress1,
            "StreetAddress2": self.StreetAddress2,
            "City": self.City,
            "State": self.State,
            "ZipCode": self.ZipCode
        }

class Manufacturer(models.Model):
    ManufacturerId = models.BigIntegerField(primary_key=True)
    Name = models.CharField(max_length=100, null=True)
    State = models.CharField(max_length=100, null=True)
    Country = models.CharField(max_length=100, null=True)
    SummaryData = models.JSONField(blank=True, null=True)
    class Meta:
        ordering = ['Name']
    
    def __str__(self):
        return str(self.Name)
    
    def serialize_manu(self):
        return {
            "Name": self.Name,
            "State": self.State,
            "Country": self.Country
        }

class TransactionItem(models.Model):
    Type_Product = models.CharField(max_length=100, null=True, blank=True)
    Category = models.CharField(max_length=100, null=True, blank=True)
    Name = models.CharField(max_length=500, null=True, blank=True)
    Opioid = models.BooleanField(default=False, blank=True, null=True)
    def __str__(self):
        return self.Type_Product + self.Name
    

class Transaction(models.Model):
    TransactionId = models.IntegerField(primary_key=True)
    Doctor = models.ForeignKey(Doctor, related_name="transactions", null=True, on_delete=models.SET_NULL)
    Manufacturer = models.ForeignKey(Manufacturer,related_name="manufacturerTransactions", null=True, on_delete=models.SET_NULL)
    transactionitems = models.ManyToManyField(TransactionItem, related_name="transactionitems")
    Pay_Amount = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    Date = models.DateField(null=True)
    Payment = models.CharField(max_length=100, null=True)
    Nature_Payment = models.CharField(max_length=200, null=True)
    Contextual_Info = models.CharField(max_length=500, null=True)
    OpioidInvolved = models.BooleanField(default=False, blank=True, null=True)
    class Meta:
        indexes = [
            models.Index(fields=['Doctor']),
            models.Index(fields=['Manufacturer']),
            models.Index(fields=['TransactionId'])
        ]
        ordering = ['-Date']
    
    def __str__(self):
        return "#{} on date {}".format(str(self.TransactionId), str(self.Date))

    def serialize_doc(self):
        return {
            "FirstName": self.Doctor.FirstName,
            "MiddleName": self.Doctor.MiddleName,
            "LastName": self.Doctor.LastName,
            "Specialty": self.Doctor.Specialty,
            "StreetAddress1": self.Doctor.StreetAddress1,
            "StreetAddress2": self.Doctor.StreetAddress2,
            "City": self.Doctor.City,
            "State": self.Doctor.State,
            "ZipCode": self.Doctor.ZipCode
        }

    def get_transactions(self):
        transactionitemsdata = []
        for x in self.transactionitems.all():
            transactionitemsdata.append({"Type_Product": x.Type_Product, "Category": x.Category, "Name": x.Name})
        return transactionitemsdata

    def serialize_summary(self):
        return {
            "Pay_Amount": self.Pay_Amount,
            "transactions": self.get_transactions(),
            "Date": self.Date,
            "Payment": self.Payment,
            "Nature_Payment": self.Nature_Payment,
            "Contextual_Info": self.Contextual_Info,
            "Manufacturer": self.Manufacturer.Name,
            "ManufacturerId": self.Manufacturer.ManufacturerId
        }
    
    