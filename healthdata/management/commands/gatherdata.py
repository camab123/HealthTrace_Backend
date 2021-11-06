from django.core.management.base import BaseCommand, CommandError
import csv
import pandas as pd
from pandas.core.indexes.base import Index
import requests
from datetime import datetime  
from tqdm import tqdm
import time
tqdm.pandas()

class Command(BaseCommand):

    def __init__(self):
        self.transaction_list = []

    def add_year(self):
        print("Enter year to collect")
        YearToCollect = input()
        print("Collecting data on year {}".format(YearToCollect))
        df = self.import_csv_data(YearToCollect)
        print("Dataset loaded in{}".format(datetime.now()))
        print("Data Cleaning Commencing... {}".format(datetime.now()))
        df = self.clean_data(df)

        print("Splitting up the Datasets {}".format(datetime.now()))
        DoctorData, ManufacturerData, TransactionData, TransactionItemData = self.split_data_for_upload(df)

        print("Cleaning Doctor Set {}".format(datetime.now()))
        doctor_df = self.clean_doctor_data(DoctorData)
        doctor_df.to_csv("healthdata/data/DoctorData{}.csv".format(YearToCollect), index=False)
        doctor_df = None

        print("Cleaning Manufacturer Set {}".format(datetime.now()))
        manufacturer_df = self.clean_manufacturer_data(ManufacturerData)
        manufacturer_df.to_csv("healthdata/data/ManufacturerData{}.csv".format(YearToCollect), index=False)
        manufacturer_df = None
        TransactionData.to_csv("healthdata/data/TransactionData{}.csv".format(YearToCollect), index=False)

        print("Cleaning TransactionItem Set {}".format(datetime.now()))
        transactionitems_df = self.clean_transactionItems_data(TransactionItemData)
        transactionitems_df.to_csv("healthdata/data/TransactionItemData{}.csv".format(YearToCollect), index=False)

        print("Getting Unique Transaction Items {}".format(datetime.now()))
        uniquetransactionitems_df = self.unique_transactionitems_data(transactionitems_df)
        uniquetransactionitems_df.to_csv("healthdata/data/UniqueTransactionItems{}.csv".format(YearToCollect), index=False)
        
        print("Finished Script {}".format(datetime.now()))

    def clean_doctor_data(self, df):
        new_cols = {}
        df = df.drop_duplicates(subset=["DoctorId"])
        DoctorColumnNames = ["DoctorId", "FirstName", "MiddleName", "LastName", "StreetAddress1", "StreetAddress2", "City", "State", "ZipCode", "Country", "Specialty"]
        for x in range(len(DoctorColumnNames)):
            new_cols[df.columns[x]] = DoctorColumnNames[x]
        df.rename(columns=new_cols, inplace=True)
        return df

    def clean_manufacturer_data(self, df):
        new_cols = {}
        df = df.drop_duplicates(subset=["ManufacturerId"])
        ManufacturerColumnNames = ["ManufacturerId", "Name", "State", "Country"]
        for x in range(len(ManufacturerColumnNames)):
            new_cols[df.columns[x]] = ManufacturerColumnNames[x]
        df.rename(columns=new_cols, inplace=True)
        return df
    
    def unique_transactionitems_data(self, df):
        df = df.drop_duplicates(subset=["Type_Product", "Category", "Name"])
        return df
    
    def clean_transactionItems_data(self, df):
        new_df = pd.DataFrame(columns=["TransactionId", "Type_Product", "Category", "Name"])
        new_data = []
        for index, row in tqdm(df.iterrows()):
            new_data.append({
                "TransactionId" : row["TransactionId"],
                "Type_Product" : row["Type_Product_1"], 
                "Category" : row["Category_1"], 
                "Name" : row["Name_1"]
                })
            new_data.append({
                "TransactionId" : row["TransactionId"],
                "Type_Product" : row["Type_Product_2"], 
                "Category" : row["Category_2"], 
                "Name" : row["Name_2"]
                })
            new_data.append({
                "TransactionId" : row["TransactionId"],
                "Type_Product" : row["Type_Product_3"], 
                "Category" : row["Category_3"], 
                "Name" : row["Name_3"]
                })
            new_data.append({
                "TransactionId" : row["TransactionId"],
                "Type_Product" : row["Type_Product_4"], 
                "Category" : row["Category_4"], 
                "Name" : row["Name_4"]
                })
            new_data.append({
                "TransactionId" : row["TransactionId"],
                "Type_Product" : row["Type_Product_5"], 
                "Category" : row["Category_5"], 
                "Name" : row["Name_5"]
                })
            if len(new_data) > 2000000:
                print("Hit limit")
                new_df = new_df.append(new_data, ignore_index=True, sort=False)
                new_data = []
        new_df = new_df.append(new_data, ignore_index=True, sort=False)
        new_df = new_df.dropna(subset = ["Type_Product", "Category", "Name"], how='all')
        return new_df

    def import_csv_data(self, year):
        BASE_URL = "https://openpaymentsdata.cms.gov/api/1/metastore/schemas/dataset/items/"
        response = requests.get(BASE_URL).json()
        transactions = {}
        for x in response:
            if x["theme"] == ["General Payments"]:
                transactions[x["keyword"][0]] = x
        for key, value in transactions.items():
            if key == str(year):
                url = value["distribution"][0]["downloadURL"]
                datatypemapping = {
                    'Physician_First_Name': object,
                    'Physician_Middle_Name': object,
                    'Physician_Last_Name': object,
                    'Recipient_Primary_Business_Street_Address_Line1': object,
                    'Recipient_Primary_Business_Street_Address_Line2': object,
                    'Recipient_City': object,
                    "Recipient_State": object, 
                    "Recipient_Zip_Code": object, 
                    "Recipient_Country": object, 
                    "Physician_Specialty": object,
                    "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name": object, 
                    "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID": object, 
                    "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_State": object, 
                    "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Country": object,
                    "Record_ID": object, 
                    'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_1': object,
                    'Product_Category_or_Therapeutic_Area_1': object,
                    'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1': object,
                    'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_2': object,
                    'Product_Category_or_Therapeutic_Area_2':object,
                    'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_2':object,
                    'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_3':object,
                    'Product_Category_or_Therapeutic_Area_3':object,
                    'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_3':object,
                    'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_4':object,
                    'Product_Category_or_Therapeutic_Area_4':object,
                    'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_4':object,
                    'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_5':object,
                    'Product_Category_or_Therapeutic_Area_5':object,
                    'Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_5':object, 
                    "Total_Amount_of_Payment_USDollars":object, 
                    "Date_of_Payment": object, 
                    "Form_of_Payment_or_Transfer_of_Value": object, 
                    "Nature_of_Payment_or_Transfer_of_Value": object, 
                    "Contextual_Information": object
                }
                Physician_Rows = ["Physician_Profile_ID", "Physician_First_Name", "Physician_Middle_Name", "Physician_Last_Name", "Recipient_Primary_Business_Street_Address_Line1", "Recipient_Primary_Business_Street_Address_Line2", "Recipient_City", "Recipient_State", "Recipient_Zip_Code", "Recipient_Country", "Physician_Specialty"]
                Manufacturer_Rows = ["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name", "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID", "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_State", "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Country"]
                Transaction_Rows = ["Record_ID", 'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_1','Product_Category_or_Therapeutic_Area_1','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_2','Product_Category_or_Therapeutic_Area_2','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_2','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_3','Product_Category_or_Therapeutic_Area_3','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_3','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_4','Product_Category_or_Therapeutic_Area_4','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_4','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_5','Product_Category_or_Therapeutic_Area_5','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_5', "Total_Amount_of_Payment_USDollars", "Date_of_Payment", "Form_of_Payment_or_Transfer_of_Value", "Nature_of_Payment_or_Transfer_of_Value", "Contextual_Information"]
                req_cols = Physician_Rows + Manufacturer_Rows + Transaction_Rows
                data = pd.read_csv(url, usecols=req_cols, dtype=datatypemapping)
                data = data[data['Physician_Profile_ID'].notna()]
                data["Physician_Profile_ID"] = data["Physician_Profile_ID"].astype("int")
                data["Total_Amount_of_Payment_USDollars"] = data["Total_Amount_of_Payment_USDollars"].astype("float")
                data["Record_ID"] = data["Record_ID"].astype("int")
                data["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"] = data["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"].astype("int")
        return data

    def clean_data(self, df):
        df = self.rename_columns(df)
        df = self.Apply_Titling(df)
        df = self.convertdatetime(df)
        return df

    def convertdatetime(self, df):
        df['Date'] = pd.to_datetime(df['Date'])
        return df

    def Apply_Titling(self, df):
        Title_Cols = ["DoctorFirstName", "DoctorMiddleName", "DoctorLastName", "DoctorStreetAddress1", "DoctorStreetAddress2", "DoctorCity","ManufacturerName", "Type_Product_1", "Category_1", "Name_1", "Type_Product_2", "Category_2", "Name_2", "Type_Product_3", "Category_3", "Name_3", "Type_Product_4", "Category_4", "Name_4", "Type_Product_5", "Category_5", "Name_5"]
        for x in Title_Cols:
            df[x] = df[x].str.title()
        return df

    def rename_columns(self, df):
        new_cols = {}
        DoctorColumnNames = ["DoctorId", "DoctorFirstName", "DoctorMiddleName", "DoctorLastName", "DoctorStreetAddress1", "DoctorStreetAddress2", "DoctorCity", "DoctorState", "DoctorZipCode", "DoctorCountry", "DoctorSpecialty"]
        ManufacturerColumnNames = ["ManufacturerId", "ManufacturerName", "ManufacturerState", "ManufacturerCountry"]
        TransactionColumnNames = ["Pay_Amount", "Date", "Form_Payment", "Nature_Payment", "Contextual_Info", "TransactionId", "Type_Product_1", "Category_1", "Name_1", "Type_Product_2", "Category_2", "Name_2", "Type_Product_3", "Category_3", "Name_3", "Type_Product_4", "Category_4", "Name_4", "Type_Product_5", "Category_5", "Name_5"]
        ColumnNames = DoctorColumnNames + ManufacturerColumnNames + TransactionColumnNames
        for x in range(len(ColumnNames)):
            new_cols[df.columns[x]] = ColumnNames[x]
        df.rename(columns=new_cols, inplace=True)
        return df
    
    def split_data_for_upload(self, df):
        DoctorColumns = ["DoctorId", "DoctorFirstName", "DoctorMiddleName", "DoctorLastName", "DoctorStreetAddress1", "DoctorStreetAddress2", "DoctorCity", "DoctorState", "DoctorZipCode", "DoctorCountry", "DoctorSpecialty"]
        ManufacturerColumns = ["ManufacturerId", "ManufacturerName", "ManufacturerState", "ManufacturerCountry"]
        TransactionColumns = ["TransactionId", "DoctorId", "ManufacturerId", "Pay_Amount", "Date", "Form_Payment", "Nature_Payment", "Contextual_Info"]
        TransactionItemColumns = ["TransactionId", "Type_Product_1", "Category_1", "Name_1", "Type_Product_2", "Category_2", "Name_2", "Type_Product_3", "Category_3", "Name_3", "Type_Product_4", "Category_4", "Name_4", "Type_Product_5", "Category_5", "Name_5"]
        DoctorFile = df[DoctorColumns]
        ManufacturerFile = df[ManufacturerColumns]
        TransactionFile = df[TransactionColumns]
        TransactionItemFile = df[TransactionItemColumns]
        return DoctorFile, ManufacturerFile, TransactionFile, TransactionItemFile

    def handle(self, *args, **kwargs):
        print("Begin script")
        self.add_year()
    
    