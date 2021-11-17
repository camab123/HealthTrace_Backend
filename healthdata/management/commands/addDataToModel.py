from django.core.management.base import BaseCommand, CommandError
import csv
import pandas as pd
from pandas.core.indexes.base import Index
import requests
from datetime import datetime
from healthdata.models import Doctor, Manufacturer, Transaction, TransactionItem
from tqdm import tqdm
import time
from django.db.models import Q, Count, Sum

import numpy as np
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

    def AddTransactionItems(self,file):
        df = pd.read_csv(file)
        print(df)
        existing_transactions = pd.DataFrame.from_records(TransactionItem.objects.all().values())
        df_all = df.merge(existing_transactions.drop_duplicates(), on=['Type_Product', 'Category', 'Name'],
                   how='left', indicator=True)
        df_all = df_all.loc[df_all['_merge'] == "left_only"]
        print(df_all)
        for index, row in df_all.iterrows():
            pass

    def MergeTransactionItemandTransaction(self):
        df = pd.read_csv("healthdata/data/all_transactionitems.csv")
        df = df.drop_duplicates()
        df = df.fillna(0)
        transactionitems = pd.DataFrame.from_records(TransactionItem.objects.all().values("id", "Type_Product", "Category", "Name"))
        transactionitems = transactionitems.replace("nan", 0)
        merged = df.merge(transactionitems, how="left", on=["Type_Product", "Category", "Name"])
        merged = merged.replace(0, np.nan)
        merged = merged[["TransactionId", "id"]]
        merged.to_csv("healthdata/data/transactiondata.csv", index=False)
        print("Finished Script")

    def addTransactionItemToTransaction(self):
        ThroughModel = Transaction.transactionitems.through
        ThroughModel.objects.all().delete()
        df = pd.read_csv("healthdata/data/ThroughModelData.csv")
        # df = df[df["TransactionId"] != 705487363]
        # df = df[df["TransactionId"] != 705487367]
        # df = df[df["TransactionId"] != 705487371]
        # df = df[df["TransactionId"] != 705487375]
        # df = df[df["TransactionId"] != 705487379]
        bulk_through = []
        for index, row in tqdm(df.iterrows()):
            bulk_through.append(ThroughModel(transaction_id = row["TransactionId"], transactionitem_id = row["id"]))
            if len(bulk_through) > 1000000:
                try:
                    ThroughModel.objects.bulk_create(bulk_through)
                    bulk_through = []
                    print("Saved")
                except:
                    print("Had to use backup method")
                    for x in bulk_through:  
                        try:
                            ThroughModel.objects.create(transaction_id = x.transaction_id, transactionitem_id = x.transactionitem_id)
                        except Exception as e:
                            print("Failed on {} due to {}".format(x, e))
                    bulk_through = []
                    print("Saved")
        ThroughModel.objects.bulk_create(bulk_through)

    def addTransactions(self):
        df = pd.read_csv("healthdata/data/NewTransactions.csv")
        bulk_items = []
        for index, row in tqdm(df.iterrows()):
            transactionobject = Transaction(TransactionId=row["TransactionId"], Doctor_id=row["DoctorId"], Manufacturer_id=row["ManufacturerId"], Pay_Amount=row["Pay_Amount"], Date=row["Date"], Payment=row["Form_Payment"], Nature_Payment=row["Nature_Payment"], Contextual_Info=row["Contextual_Info"], OpioidInvolved=False)
            bulk_items.append(transactionobject)
            if len(bulk_items) > 30000:
                Transaction.objects.bulk_create(bulk_items)
                bulk_items = []
        Transaction.objects.bulk_create(bulk_items)

    def TransactionByCounty(self):
        df = pd.read_csv("healthdata/data/CountytoDoc.csv", dtype={"CountyId": str})
        print(df["CountyId"])
        data = []
        df["DoctorId"] = df["DoctorId"].apply(lambda x: x[1:-1].split(','))
        for index, row in tqdm(df.iterrows()):
            print(row["CountyId"])
            doctors = row["DoctorId"]
            transactions = Transaction.objects.filter(Doctor__in=doctors).values("Date", "Pay_Amount", "OpioidInvolved")
            OpioidData = transactions.filter(OpioidInvolved=True).values("Date", "Pay_Amount", "OpioidInvolved")
            OverallSum = transactions.aggregate(Sum("Pay_Amount"))
            OpioidSum = OpioidData.aggregate(Sum("Pay_Amount"))
            if OpioidSum["Pay_Amount__sum"] is None:
                OpioidSum["Pay_Amount__sum"] = 0
            if OverallSum["Pay_Amount__sum"] is None:
                OverallSum["Pay_Amount__sum"] = 0
            data.append({
                "County": row["CountyId"],
                "TransactionSum": OverallSum["Pay_Amount__sum"],
                "OpioidSum": OpioidSum["Pay_Amount__sum"]
            })
            if index == 10:
                df = pd.DataFrame.from_dict(data)
                print(df)
                break
        df = pd.DataFrame.from_dict(data)
        df.to_csv("CountyDrugData.csv", index=False)

    def handle(self, *args, **kwargs):
        print("Begin script")
        self.TransactionByCounty()
