from os import stat
from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from pandas.core.indexes.base import Index
from datetime import datetime  
from tqdm import tqdm
import json
from django.db.models.aggregates import Max
from django.db.models import Count, Sum, query, Prefetch
from alive_progress import alive_bar
from healthdata.models import Doctor, Transaction, TransactionItem
import re
tqdm.pandas()

class Command(BaseCommand):
    
    def CountyJson(self):
        jsonfile = open("healthdata/data/counties-10m.json",)
        data = json.load(jsonfile)
        df = pd.read_csv("healthdata/data/countyToStateData.csv", dtype={"County": str})
        failed = []
        for x in data["objects"]["counties"]["geometries"]:
            countyid = x["id"]
            datarow = df[df["County"] == countyid]
            try:
                TransactionSum = datarow["TransactionSum"].values[0]
                OpioidSum = datarow["OpioidSum"].values[0]
                State = datarow["State"].values[0]
                properties = x["properties"]
                properties["TransactionSum"] = TransactionSum
                properties["OpioidSum"] = OpioidSum
                properties["State"] = State
            except:
                properties = x["properties"]
                properties["TransactionSum"] = None
                properties["OpioidSum"] = None
                properties["State"] = None
        with open('healthdata/data/countiesdata.json', 'w') as outfile:
            json.dump(data, outfile)

    def GetState(self):
        jsonfile = open("healthdata/data/countiesdata.json",)
        data = json.load(jsonfile)
        counties = [x for x in data["objects"]["counties"]["geometries"] if x["properties"]["State"] == "VA"]
        data["objects"]["counties"]["geometries"] = counties
        with open('healthdata/data/teststate.json', 'w') as outfile:
            json.dump(data, outfile)

    def GenerateStylingNulls(self):
        jsonfile = open("healthdata/data/StateTransformations.json")
        data = json.load(jsonfile)
        states = open("healthdata/data/countiesdata.json",)
        states = json.load(states)
        statelist = [x["properties"]["State"] for x in states["objects"]["counties"]["geometries"]]
        statelist = list(set(statelist))
        statelist.remove(None)
        newdict = {}
        for x in sorted(statelist):
            newdict[x] = "null"
        with open('healthdata/data/StateStyling.json', 'w') as outfile:
            json.dump(newdict, outfile, indent=2)

    def generateStateFiles(self, state):
        jsonfile = open("healthdata/data/countiesdata.json",)
        transformationsfile = open("healthdata/data/StateTransformations.json")
        data = json.load(jsonfile)
        transformations = json.load(transformationsfile)
        transformation = transformations[state]
        counties = [x for x in data["objects"]["counties"]["geometries"] if x["properties"]["State"] == state]
        data["objects"]["counties"]["geometries"] = counties
        file_data = {
            "Transformations": transformation, 
            "GeoJson": data,
            "SummaryData": {}
        }
        with open("healthdata/data/statedata/{}.json".format(state), "w") as f:
            summarydata = json.load(f)
            print(len(summarydata["SummaryData"]))
            # years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, None]
            # for x in years:
            #     querydata, year = self.getStateQueryData(state, x)
            #     file_data["SummaryData"][year] = querydata
            # json.dump(file_data, f)

    def getStateQueryData(self, state, year):
        data = {}
        if year:
            transactions = Transaction.objects.filter(Doctor__in=Doctor.objects.filter(State=state), Date__year=year).prefetch_related("transactionitems").select_related("Manufacturer")
        else:
            transactions = Transaction.objects.filter(Doctor__in=Doctor.objects.filter(State=state)).prefetch_related("transactionitems").select_related("Manufacturer")
        SumPayment = transactions.aggregate(Sum("Pay_Amount"))
        SumPaymentJson = SumPayment["Pay_Amount__sum"]
        if SumPaymentJson:
            SumPaymentJson = float(SumPaymentJson)
        TopManufacturers = transactions.values("Manufacturer__ManufacturerId", "Manufacturer__Name").annotate(top_manufacturers=Sum("Pay_Amount")).order_by("-top_manufacturers")[:10]
        TopManufacturersJson = []
        for x in TopManufacturers:
            TopManufacturersJson.append(
                    {
                        "ManufacturerId": x["Manufacturer__ManufacturerId"],
                        "ManufacturerName": x["Manufacturer__Name"],
                        "PayAmount": float(x["top_manufacturers"])
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
        data = {
            "Sum_Payments": SumPaymentJson,
            "Top_Doctors": TopDoctorsJson,
            "Most_Common_Items": MostCommonDrugsJson,
            "Top_Items": TopItemPaymentsJson,
            "Top_Manufacturers": TopManufacturersJson,
            }
        return data, year

    def handle(self, *args, **kwargs):
        print("Begin script")
        with open("healthdata/data/StateTransformations.json", "r") as json_file:
            data = json.load(json_file)
            with alive_bar(len(data.items())) as bar:
                for key, value in data.items():
                    print(key)
                    self.generateStateFiles(key)
                    bar()
        