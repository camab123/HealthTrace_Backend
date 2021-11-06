from django.core.management.base import BaseCommand, CommandError
from healthdata.models import Doctor, Manufacturer, Transaction, TransactionItem
import csv
import pandas as pd
from datetime import datetime
import requests
import sys
import urllib.request
from django.db import transaction
from django.db.models import Q
from alive_progress import alive_bar
from itertools import groupby
from tqdm import tqdm
import time
tqdm.pandas()


class Command(BaseCommand):

    def __init__(self):
        self.transaction_list = []

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
            Physician_Rows = ["Physician_Profile_ID", "Physician_First_Name", "Physician_Middle_Name", "Physician_Last_Name", "Recipient_Primary_Business_Street_Address_Line1", "Recipient_Primary_Business_Street_Address_Line2", "Recipient_City", "Recipient_State", "Recipient_Zip_Code", "Recipient_Country", "Physician_Specialty"]
            Manufacturer_Rows = ["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name", "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID", "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_State", "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Country"]
            Transaction_Rows = ["Record_ID", 'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_1','Product_Category_or_Therapeutic_Area_1','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_2','Product_Category_or_Therapeutic_Area_2','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_2','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_3','Product_Category_or_Therapeutic_Area_3','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_3','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_4','Product_Category_or_Therapeutic_Area_4','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_4','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_5','Product_Category_or_Therapeutic_Area_5','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_5' "Total_Amount_of_Payment_USDollars", "Date_of_Payment", "Form_of_Payment_or_Transfer_of_Value", "Nature_of_Payment_or_Transfer_of_Value", "Contextual_Information"]
            req_cols = Physician_Rows + Manufacturer_Rows + Transaction_Rows
            df = pd.read_csv("healthdata/data/transactions/{}.csv".format(year), usecols=req_cols)
            # if Transaction.objects.filter(pk=first_row["Record_ID"]):
            #     print("Already added")
            # else:
            #     print("Not added")
            print("{} is length of dataset".format(len(df.index)))
            with alive_bar(len(df.index)) as bar:
                for index, row in df.iterrows():
                    if len(self.transaction_list) > 100000:
                        Transaction.objects.bulk_create(self.transaction_list)
                        self.transaction_list = []
                    transaction = Transaction(
                    TransactionId=row["Record_ID"],
                    Doctor_id = row["Physician_Profile_ID"],
                    Manufacturer_id = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"],

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
                    Date = row["Date_of_Payment"],
                    Payment = row["Form_of_Payment_or_Transfer_of_Value"],
                    Nature_Payment = row["Nature_of_Payment_or_Transfer_of_Value"],
                    Contextual_Info = row["Contextual_Information"]
                    )
                    self.transaction_list.append(transaction)
                    bar()
            Transaction.objects.bulk_create(self.transaction_list)
            print("Upload complete")

        elif data == "transactionitems":
            req_cols = ["Type_Product", "Category", "Name"]
            df = pd.read_csv("healthdata/data/all_items.csv", usecols=req_cols)
            for index, row in df.iterrows():
                item = TransactionItem.objects.get_or_create(
                    Type_Product = row["Type_Product"],
                    Category = row["Category"],
                    Name = row["Name"]
                )
        else:
            print("Inputted wrong string use (doctors, manafacturers, or transactions)")

    def create_transaction_record(self, row):
        print(self.transaction_list)
        transaction = Transaction(
                TransactionId=row["Record_ID"],
                Doctor_id = row["Physician_Profile_ID"],
                Manufacturer_id = row["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"],

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
                Date = row["Date_of_Payment"],
                Payment = row["Form_of_Payment_or_Transfer_of_Value"],
                Nature_Payment = row["Nature_of_Payment_or_Transfer_of_Value"],
                Contextual_Info = row["Contextual_Information"]
            )
        return transaction

    def add_transaction_items(self):
        transactions = Transaction.objects.filter(transactionitems__isnull=True).only(
            "Type_Product_1", 
            "Category_1", 
            "Name_1",
            "Type_Product_2", 
            "Category_2", 
            "Name_2",
            "Type_Product_3", 
            "Category_3", 
            "Name_3",
            "Type_Product_4", 
            "Category_4", 
            "Name_4",
            "Type_Product_5", 
            "Category_5", 
            "Name_5",
            "transactionitems"
        )
        # with alive_bar(len(transactions)) as bar:
        ThroughModel = Transaction.transactionitems.through
        bulk_through = []
        #480 avg
        #522 it/s
        #580 it/s
        for x in tqdm(transactions):
            query = Q()
            query_items = []
            if x.Type_Product_1 != "nan" and x.Category_1 != "nan" and x.Name_1 != "nan":
                query_items.append([x.Type_Product_1, x.Category_1, x.Name_1])

                if x.Type_Product_2 != "nan" and x.Category_2 != "nan" and x.Name_2 != "nan":
                    query_items.append([x.Type_Product_2, x.Category_2, x.Name_2])

                    if x.Type_Product_3 != "nan" and x.Category_3 != "nan" and x.Name_3 != "nan":
                        query_items.append([x.Type_Product_3, x.Category_3, x.Name_3])

                        if x.Type_Product_4 != "nan" and x.Category_4 != "nan" and x.Name_4 != "nan":
                            query_items.append([x.Type_Product_4, x.Category_4, x.Name_4])

                            if x.Type_Product_5 != "nan" and x.Category_5 != "nan" and x.Name_5 != "nan":
                                query_items.append([x.Type_Product_5, x.Category_5, x.Name_5])
            if len(query_items) == 0:
                bulk_through.append(ThroughModel(transaction_id = x.pk, transactionitem_id = 3))
            else:
                for item in query_items:
                    query |= Q(Type_Product=item[0], Category=item[1], Name=item[2])
                for y in TransactionItem.objects.filter(query).only("id"):
                    bulk_through.append(ThroughModel(transaction_id = x.pk, transactionitem_id = y.pk))
            if len(bulk_through) > 300000:
                ThroughModel.objects.bulk_create(bulk_through)
                bulk_through = []
                print("Saved")
        ThroughModel.objects.bulk_create(bulk_through)

    def delete_transaction_items(self):
        items = Transaction.transactionitems.through.objects.filter(transactionitem_id = 3)
        print(len(items))

    def capitalize_transaction_items(self):
        transactionitems = TransactionItem.objects.all()
        for x in transactionitems:
            x.Type_Product = x.Type_Product.capitalize()
            x.Category = x.Category.capitalize()
            x.Name = x.Name.capitalize()
            x.save(update_fields=['Type_Product', 'Category', 'Name'])

    def fix_addresses(self):
        doctors = Doctor.objects.all()
        for x in doctors:
            x.StreetAddress1 = x.StreetAddress1.title()
            x.StreetAddress2 = x.StreetAddress2.title()
            x.save(update_fields=["StreetAddress1", "StreetAddress2"])

    def handle(self, *args, **kwargs):
        data = kwargs["dataset"]
        year = kwargs["year"]
        self.create_statsdf_manufacturer()
        #11973177 are device transactions
        #40013984 are drug transactions
        #self.add_data(data, year)
        
        
            

