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

    def AddManufacturers(self):
        df = self.getManufacturerData()
        ManufacturerColumnNames = ["ManufacturerId", "ManufacturerName", "ManufacturerState", "ManufacturerCountry"]
        ManufacturerTitlingCols = ["ManufacturerName", "ManufacturerCountry"]
        print("Cleaning Manufacturer Set {}".format(datetime.now()))
        df = self.clean_data(df, ManufacturerColumnNames, ManufacturerTitlingCols)
        df.to_csv("healthdata/data/ManufacturerData.csv", index=False)

    def AddDoctors(self):
        df = self.getDoctorData()
        DoctorColumnNames = ["DoctorId", "DoctorFirstName", "DoctorMiddleName", "DoctorLastName", "DoctorStreetAddress1", "DoctorStreetAddress2", "DoctorCity", "DoctorState", "DoctorZipCode", "DoctorCountry", "DoctorSpecialty"]
        DoctorTitlingCols = ["DoctorFirstName", "DoctorMiddleName", "DoctorLastName", "DoctorStreetAddress1", "DoctorStreetAddress2", "DoctorCity", "DoctorCountry"]
        print("Cleaning Doctor Set {}".format(datetime.now()))
        df = self.clean_data(df, DoctorColumnNames, DoctorTitlingCols)
        df.to_csv("healthdata/data/DoctorData.csv", index=False)

    def AddTransactionYear(self):
        print("Enter year to collect")
        YearToCollect = input()
        print("Collecting data on year {}".format(YearToCollect))
        df = self.getTransactionData(YearToCollect)
        print("Dataset loaded in{}".format(datetime.now()))
        print("Data Cleaning Commencing... {}".format(datetime.now()))
        TransactionColumnNames = ["DoctorId", "ManufacturerId", "Pay_Amount", "Date", "Form_Payment", "Nature_Payment", "Contextual_Info", "TransactionId", "Type_Product_1", "Category_1", "Name_1", "Type_Product_2", "Category_2", "Name_2", "Type_Product_3", "Category_3", "Name_3", "Type_Product_4", "Category_4", "Name_4", "Type_Product_5", "Category_5", "Name_5"]
        TransactionTitleCols = ["Type_Product_1", "Category_1", "Name_1", "Type_Product_2", "Category_2", "Name_2", "Type_Product_3", "Category_3", "Name_3", "Type_Product_4", "Category_4", "Name_4", "Type_Product_5", "Category_5", "Name_5"]
        df = self.clean_data(df, TransactionColumnNames, TransactionTitleCols)
        df = self.convertdatetime(df)
        print("Splitting up the Datasets {}".format(datetime.now()))
        TransactionData, TransactionItemData = self.split_data_for_upload(df)   
        TransactionData.to_csv("healthdata/data/TransactionData{}.csv".format(YearToCollect), index=False)

        print("Cleaning TransactionItem Set {}".format(datetime.now()))
        transactionitems_df = self.clean_transactionItems_data(TransactionItemData)
        transactionitems_df.to_csv("healthdata/data/TransactionItemData{}.csv".format(YearToCollect), index=False)

        print("Getting Unique Transaction Items {}".format(datetime.now()))
        uniquetransactionitems_df = self.unique_transactionitems_data(transactionitems_df)
        uniquetransactionitems_df.to_csv("healthdata/data/UniqueTransactionItems{}.csv".format(YearToCollect), index=False)
        
        print("Finished Script {}".format(datetime.now()))
    
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

    def getDoctorData(self):
        url = "https://download.cms.gov/openpayments/SMRY_P06302021/pblctn-physn-prfl-srch-p06302021-06152021.92tc-vif6.csv"
        req_cols = [
            "Physician_Profile_ID",
            "Physician_Profile_First_Name",
            "Physician_Profile_Middle_Name",
            "Physician_Profile_Last_Name",
            "Physician_Profile_Address_Line_1",
            "Physician_Profile_Address_Line_2",
            "Physician_Profile_City",
            "Physician_Profile_State",
            "Physician_Profile_Zipcode",
            "Physician_Profile_Country_Name",
            "Physician_Profile_Primary_Specialty"
        ]
        data = pd.read_csv(url, usecols=req_cols)
        data["Physician_Profile_ID"] = data["Physician_Profile_ID"].astype(int)
        return data

    def getManufacturerData(self):
        url = "https://download.cms.gov/openpayments/SMRY_P06302021/pblctn-rptg-org-prfl-srch-p06302021-06152021.4p5f-g6a9.csv"
        req_cols = [
            "AMGPO_Making_Payment_ID",
            "AMGPO_Making_Payment_Name",
            "AMGPO_Making_Payment_State",
            "AMGPO_Making_Payment_Country"
        ]
        data = pd.read_csv(url, usecols=req_cols)
        data["AMGPO_Making_Payment_ID"] = data["AMGPO_Making_Payment_ID"].astype("int")
        return data

    def getTransactionData(self, year):
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
                    "Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID": object, 
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
                Physician_Rows = ["Physician_Profile_ID"]
                Manufacturer_Rows = ["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"]
                Transaction_Rows = ["Record_ID", 'Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_1','Product_Category_or_Therapeutic_Area_1','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_1','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_2','Product_Category_or_Therapeutic_Area_2','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_2','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_3','Product_Category_or_Therapeutic_Area_3','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_3','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_4','Product_Category_or_Therapeutic_Area_4','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_4','Indicate_Drug_or_Biological_or_Device_or_Medical_Supply_5','Product_Category_or_Therapeutic_Area_5','Name_of_Drug_or_Biological_or_Device_or_Medical_Supply_5', "Total_Amount_of_Payment_USDollars", "Date_of_Payment", "Form_of_Payment_or_Transfer_of_Value", "Nature_of_Payment_or_Transfer_of_Value", "Contextual_Information"]
                req_cols = Physician_Rows + Manufacturer_Rows + Transaction_Rows
                data = pd.read_csv(url, usecols=req_cols, dtype=datatypemapping)
                data = data[data['Physician_Profile_ID'].notna()]
                data["Physician_Profile_ID"] = data["Physician_Profile_ID"].astype("int")
                data["Total_Amount_of_Payment_USDollars"] = data["Total_Amount_of_Payment_USDollars"].astype("float")
                data["Record_ID"] = data["Record_ID"].astype("int")
                data["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"] = data["Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_ID"].astype("int")
        return data

    def clean_data(self, df, renamecols, titlingcols):
        df = self.rename_columns(df, renamecols)
        df = self.Apply_Titling(df, titlingcols)
        return df

    def convertdatetime(self, df):
        df['Date'] = pd.to_datetime(df['Date'])
        return df

    def Apply_Titling(self, df, titlingcols):
        for x in titlingcols:
            print(x)
            df[x] = df[x].str.title()
        return df

    def rename_columns(self, df, renamecols):
        new_cols = {}
        for x in range(len(renamecols)):
            new_cols[df.columns[x]] = renamecols[x]
        df.rename(columns=new_cols, inplace=True)
        return df
    
    def split_data_for_upload(self, df):
        TransactionColumns = ["TransactionId", "DoctorId", "ManufacturerId", "Pay_Amount", "Date", "Form_Payment", "Nature_Payment", "Contextual_Info"]
        TransactionItemColumns = ["TransactionId", "Type_Product_1", "Category_1", "Name_1", "Type_Product_2", "Category_2", "Name_2", "Type_Product_3", "Category_3", "Name_3", "Type_Product_4", "Category_4", "Name_4", "Type_Product_5", "Category_5", "Name_5"]
        TransactionFile = df[TransactionColumns]
        TransactionItemFile = df[TransactionItemColumns]
        return TransactionFile, TransactionItemFile

    def handle(self, *args, **kwargs):
        print("Begin script")
        self.AddTransactionYear()
    
    