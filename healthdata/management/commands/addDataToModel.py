from django.core.management.base import BaseCommand, CommandError
import csv
import pandas as pd
from pandas.core.indexes.base import Index
import requests
from datetime import datetime  
from healthdata.models import Doctor, Manufacturer, Transaction, TransactionItem
from tqdm import tqdm
import time
tqdm.pandas()

class Command(BaseCommand):

    def __init__(self):
        pass
    
    def UpdateDoctorData(self, file):
        df = pd.read_csv(file)
        existing_doctors = pd.DataFrame.from_records(Doctor.objects.all().values())
        df_all = df.merge(existing_doctors.drop_duplicates(), on=['DoctorId'], 
                   how='left', indicator=True)
        df_all = df_all.loc[df_all['_merge'] == "left_only"]
        for index, row in df_all.iterrows():
            doctor = Doctor(DoctorId=row["DoctorId"], FirstName=row["DoctorFirstName"], MiddleName=row["DoctorMiddleName"], LastName=row["DoctorLastName"], StreetAddress1=row["DoctorStreetAddress1"], StreetAddress2=row["DoctorStreetAddress2"], City=row["DoctorCity"], State=row["DoctorState"], ZipCode=row["DoctorZipCode"], Country=row["DoctorCountry"], Specialty=row["DoctorSpecialty"])
            print(doctor)

    def UpdateManufacturerData(self, file):
        df = pd.read_csv(file)
        existing_manufacturers = pd.DataFrame.from_records(Manufacturer.objects.all().values("ManufacturerId"))
        df_all = df.merge(existing_manufacturers.drop_duplicates(), on=['ManufacturerId'], 
                   how='left', indicator=True)
        df_all = df_all.loc[df_all['_merge'] == "left_only"]
        for index, row in df_all.iterrows():
            manufacturer = Manufacturer(ManufacturerId=row["ManufacturerId"], Name=row["ManufacturerName"], State=row["ManufacturerState"], Country=row["ManufacturerCountry"])
            manufacturer.save()
    
    def AddTransactionYear(self, file):
        df = pd.read_csv(file)
        for index, row in df.iterrows():
            transaction = Transaction(TransactionId=row["TransactionId"], Doctor=Doctor.objects.get(pk=row["DoctorId"]), Manufacturer=Manufacturer.objects.get(pk=row["ManufacturerId"]), Pay_Amount=row["Pay_Amount"], Date=row["Date"], Payment=row["Form_Payment"], Nature_Payment=row["Nature_Payment"], Contextual_Info=row["Contextual_Info"], OpioidInvolved=False)
            transaction.save()

    def AddTransactionItemsToTransactions(self, file):
        df = pd.read_csv(file)
        for index, row in df.iterrows():
            transaction = Transaction.objects.get(pk=row["TransactionId"])
            transactionitem = TransactionItem.objects.filter(Type_Product=row["Type_Product"]).filter(Category=row["Category"]).filter(Name=row["Name"])
            if len(transactionitem) > 1:
                print(transactionitem.values())
            # print(transactionitem.values())
            # print(transaction)
            

    def handle(self, *args, **kwargs):
        print("Begin script")
        self.AddTransactionItemsToTransactions("healthdata/data/TransactionItemData2020.csv")
    