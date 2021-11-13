from django.core.management.base import BaseCommand, CommandError
from healthdata.models import Doctor, Manufacturer, Transaction, TransactionItem
import csv
import pandas as pd
from datetime import date, datetime
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
from django.db.models.aggregates import Max
from django.db.models import Count, Sum, query, Prefetch
import re
import json


class Command(BaseCommand):

    def __init__(self):
        self.objectjson = {}

    def ModelJsonPost(self, id):
        
        years = [2016, 2017, 2018, 2019, 2020, None]
        for x in years:
            self.GetModelData(id, x)
        manufacturer = Manufacturer.objects.get(pk=id)
        manufacturer.SummaryData = self.objectjson
        manufacturer.save()
    def GetModelData(self, id, year):
        manufacturer = Manufacturer.objects.get(pk=id)
        if year:
            transactions = Transaction.objects.filter(Manufacturer=manufacturer, Date__year=year).prefetch_related("transactionitems").select_related("Doctor")
        else:
            transactions = Transaction.objects.filter(Manufacturer=manufacturer).prefetch_related("transactionitems").select_related("Doctor")
        SumPayment = transactions.aggregate(Sum("Pay_Amount"))
        SumPaymentJson = SumPayment["Pay_Amount__sum"]
        if SumPaymentJson:
            SumPaymentJson = float(SumPaymentJson)
        TopStates = transactions.values("Doctor__State").annotate(top_states=Sum("Pay_Amount")).order_by("-top_states")[:10]
        TopStatesJson = []
        for x in TopStates:
            TopStatesJson.append(
                {
                    "State": x["Doctor__State"],
                    "Amount": float(x["top_states"])
                }
            )
        
        TopDoctors = transactions.values("Doctor__DoctorId", "Doctor__FirstName", "Doctor__MiddleName", "Doctor__LastName").annotate(top_docs=Sum("Pay_Amount")).order_by("-top_docs")[:10]
        TopDoctorsJson = []
        for x in TopDoctors:
            TopDoctorsJson.append(
                    {
                        "DoctorId": x["Doctor__DoctorId"],
                        "DoctorName": re.sub(' +', ' ', x["Doctor__FirstName"] + " " + x["Doctor__MiddleName"] + " " + x["Doctor__LastName"]),
                        "PayAmount": float(x["top_docs"])
                    }
                )
        
        LargestPayoffs = transactions.values("Doctor__DoctorId", "Doctor__FirstName", "Doctor__MiddleName", "Doctor__LastName", "Pay_Amount", "TransactionId").order_by("-Pay_Amount")[:10]
        LargestPayoffsJson = []
        for x in LargestPayoffs:
            LargestPayoffsJson.append(
                {
                    "PayAmount": float(x["Pay_Amount"]),
                    "DoctorName": re.sub(' +', ' ', x["Doctor__FirstName"] + " " + x["Doctor__MiddleName"] + " " + x["Doctor__LastName"]),
                    "TransactionId": x["TransactionId"],
                    "DoctorId": x["Doctor__DoctorId"],
                }
            )
        transactionitemsquery = TransactionItem.objects.exclude(Name__isnull=True).filter(transactionitems__in=transactions).values("Type_Product", "Name")
        MostCommonDrugs = transactionitemsquery.annotate(top_drugs=Count('Name')).order_by('-top_drugs')[:10]
        MostCommonDrugsJson = []
        for x in MostCommonDrugs:
            MostCommonDrugsJson.append(
                {
                    "Type_Product": x["Type_Product"],
                    "Name": x["Name"],
                    "Count": x["top_drugs"]
                }
            )
        TopItemPayments = transactionitemsquery.annotate(total=Sum('transactionitems__Pay_Amount')).order_by('-total')[:10]
        TopItemPaymentsJson = []
        for x in TopItemPayments:
            TopItemPaymentsJson.append(
                {
                    "Type_Product": x["Type_Product"],
                    "Name": x["Name"],
                    "TotalPay": float(x["total"])
                }
            )
        if not year:
            year = "All"
        self.objectjson[year] = {
            "Sum_Payments": SumPaymentJson,
            "Top_Doctors": TopDoctorsJson,
            "Largest_Payments": LargestPayoffsJson,
            "Most_Common_Items": MostCommonDrugsJson,
            "Top_Items": TopItemPaymentsJson,
            "Top_States": TopStatesJson,
            }
    def handle(self, *args, **kwargs):
        all_manufacturers = Manufacturer.objects.all().values("ManufacturerId")
        with alive_bar(len(all_manufacturers)) as bar:
            for x in all_manufacturers:
                self.ModelJsonPost(x["ManufacturerId"])
                bar()