from django.core.management.base import BaseCommand, CommandError
from healthdata.models import Doctor, Manufacturer, Transaction
import csv
import pandas as pd
from datetime import datetime
import requests
import sys
import urllib.request
from alive_progress import alive_bar



class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("dataset", type=str, help="data to pull (doctors, manufacturers, transactions")
        parser.add_argument("year", type=str, help="clarify year for transactions")
    def add_data(self, data, year):
        if data == "doctors":
            df = pd.read_csv("healthdata/data/doctors.csv")
            if "Unnamed: 0" in df.columns:
                df = df.drop(["Unnamed: 0"], axis=1)
            df = df.fillna('')
            print("Adding to Doctor Records")
            Doctor.objects.all().delete()
            for index, row in df.iterrows():
                doctor = Doctor.objects.get_or_create(
                    DoctorId=row["Physician_Profile_ID"],
                    FirstName=row["Physician_Profile_First_Name"],
                    MiddleName=row["Physician_Profile_Middle_Name"], 
                    LastName=row["Physician_Profile_Last_Name"],
                    Specialty=row["Physician_Profile_Primary_Specialty"],
                    StreetAddress1=row["Physician_Profile_Address_Line_1"],
                    StreetAddress2=row["Physician_Profile_Address_Line_2"],
                    City=row["Physician_Profile_City"],
                    State=row["Physician_Profile_State"],
                    ZipCode=row["Physician_Profile_Zipcode"],
                    Country=row["Physician_Profile_Country_Name"]
                )
        elif data == "manufacturers":
            print("Adding to Manufacturer Records")
            df = pd.read_csv("healthdata/data/manufacturers.csv")
            if "Unnamed: 0" in df.columns:
                df = df.drop(["Unnamed: 0"], axis=1)
            df = df.fillna('')
            Manufacturer.objects.all().delete()
            for index, row in df.iterrows():
                manufacturer, create = Manufacturer.objects.get_or_create(
                    ManufacturerId = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"],
                    Name = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name"],
                    State = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_State"],
                    Country = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Country"]
                )
        elif data == "transactions":
            print("Adding to Transaction Records")
            req_cols = ['Physician_Profile_ID',
                        'Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID',
                        'Total_Amount_of_Payment_USDollars', 'Date_of_Payment',
                        'Form_of_Payment_or_Transfer_of_Value',
                        'Nature_of_Payment_or_Transfer_of_Value', 'Contextual_Information',
                        'Record_ID',
                        'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_1',
                        'Product_Category_or_Therapeutic_Area_1',
                        'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1',
                        'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_2',
                        'Product_Category_or_Therapeutic_Area_2',
                        'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_2',
                        'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_3',
                        'Product_Category_or_Therapeutic_Area_3',
                        'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_3',
                        'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_4',
                        'Product_Category_or_Therapeutic_Area_4',
                        'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_4',
                        'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_5',
                        'Product_Category_or_Therapeutic_Area_5',
                        'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_5']
            df = pd.read_csv("healthdata/data/transactions/{}.csv".format(year), usecols=req_cols)
            print("{} is length of dataset".format(len(df.index)))
            with alive_bar(len(df.index)) as bar:
                for index, row in df.iterrows():
                    transaction, created = Transaction.objects.get_or_create(
                        TransactionId=row["Record_ID"],
                        Doctor = Doctor.objects.get(pk=row["Physician_Profile_ID"]),
                        Manufacturer = Manufacturer.objects.get(pk=row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"]),

                        Type_Product_1 = row["Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_1"],
                        Category_1 = row["Product_Category_or_Therapeutic_Area_1"],
                        Name_1 = row["Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1"],

                        Type_Product_2 = row["Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_2"],
                        Category_2 = row["Product_Category_or_Therapeutic_Area_2"],
                        Name_2 = row["Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_2"],

                        Type_Product_3 = row["Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_3"],
                        Category_3 = row["Product_Category_or_Therapeutic_Area_3"],
                        Name_3 = row["Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_3"],

                        Type_Product_4 = row["Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_4"],
                        Category_4 = row["Product_Category_or_Therapeutic_Area_4"],
                        Name_4 = row["Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_4"],

                        Type_Product_5 = row["Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_5"],
                        Category_5 = row["Product_Category_or_Therapeutic_Area_5"],
                        Name_5 = row["Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_5"],

                        Pay_Amount = row["Total_Amount_of_Payment_USDollars"],
                        Date = datetime.strptime(row["Date_of_Payment"], '%m/%d/%Y'),
                        Payment = row["Form_of_Payment_or_Transfer_of_Value"],
                        Nature_Payment = row["Nature_of_Payment_or_Transfer_of_Value"],
                        Contextual_Info = row["Contextual_Information"]
                    )
                    bar()
        else:
            print("Inputted wrong string use (doctors, manafacturers, or transactions)")

    def download_data(self, type):
        BASE_URL = "https://openpaymentsdata.cms.gov/api/1/metastore/schemas/dataset/items/"
        response = requests.get(BASE_URL).json()
        transactions = []
        for x in response:
            if x["theme"] == ["General Payments"]:
                transactions.append(x)
        for x in transactions:
            url = x["distribution"][0]["downloadURL"]
            data = pd.read_csv(url)
            # with urllib.request.urlopen(url) as f:
            #      html = f.read().decode('utf-8')
            print(data)
            break

    def handle(self, *args, **kwargs):
        data = kwargs["dataset"]
        year = kwargs["year"]
        self.add_data(data, year)
        
        
            

