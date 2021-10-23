from django.core.management.base import BaseCommand, CommandError
from healthdata.models import Doctor, Manafacturer, Transaction
import csv
import pandas as pd
from datetime import datetime



class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("newData", type=bool, help="Pull in new dataset")
        parser.add_argument("dataset", type=str, help="data to pull (doctors, manufacturers, transactions")

    def handle(self, *args, **kwargs):
        newData = kwargs["newData"]
        data = kwargs["dataset"]
        df = pd.read_csv("healthdata/data/{}.csv".format(data))
        if "Unnamed: 0" in df.columns:
            df = df.drop(["Unnamed: 0"], axis=1)
        if data == "doctors":
            Doctor.objects.all().delete()
            for index, row in df.iterrows():
                doctor = Doctor(
                    DoctorId=row["Physician_Profile_ID"],
                    FirstName=row["Physician_First_Name"],
                    MiddleName=row["Physician_Middle_Name"], 
                    LastName=row["Physician_Last_Name"],
                    PrimaryType=row["Physician_Primary_Type"],
                    Specialty=row["Physician_Specialty"],
                    StreetAddress1=row["Recipient_Primary_Business_Street_Address_Line1"],
                    StreetAddress2=row["Recipient_Primary_Business_Street_Address_Line2"],
                    City=row["Recipient_City"],
                    State=row["Recipient_State"],
                    ZipCode=row["Recipient_Zip_Code"],
                    Country=row["Recipient_Country"]
                )
                doctor.save()
        elif data == "manufacturers":
            Manafacturer.objects.all().delete()
            for index, row in df.iterrows():
                manafacturer = Manafacturer(
                    ManafacturerId = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"],
                    Name = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name"],
                    State = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_State"],
                    Country = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Country"]
                )
                manafacturer.save()
        elif data == "drug_transactions":
            Transaction.objects.all().delete()
            for index, row in df.iterrows():
                transaction = Transaction(
                    TransactionId=row["Record_ID"],
                    Doctor = Doctor.objects.get(pk=row["Physician_Profile_ID"]),
                    Manafacturer = Manafacturer.objects.get(pk=row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"]),
                    Type_Product = row["Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_1"],
                    Category = row["Product_Category_or_Therapeutic_Area_1"],
                    Name = row["Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1"],
                    Pay_Amount = row["Total_Amount_of_Payment_USDollars"],
                    Date = datetime.strptime(row["Date_of_Payment"], '%m/%d/%Y'),
                    Payment = row["Form_of_Payment_or_Transfer_of_Value"],
                    Nature_Payment = row["Nature_of_Payment_or_Transfer_of_Value"],
                    Contextual_Info = row["Contextual_Information"]
                )
                transaction.save()
        else:
            print("Inputted wrong string use (doctors, manafacturers, or transactions)")
        
        
    

