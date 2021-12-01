from os import stat
from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from pandas.core.indexes.base import Index
from datetime import datetime  
from tqdm import tqdm
import json
from django.db.models.aggregates import Max
from django.db.models import Count, Sum, query, Prefetch, F
from alive_progress import alive_bar
from healthdata.models import Doctor, Transaction, TransactionItem, State
from django.db.models.expressions import RawSQL
from django.db.models.expressions import Window
from django.db.models.functions import Rank
import re
tqdm.pandas()

class Command(BaseCommand):
    
    def __init__(self):
        self.summaryjson = {}
        self.summaryOpioidJson = {}

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

    def createStateModels(self, state):
        us_state_to_abbrev = {
        "Alabama": "AL",
        "Alaska": "AK",
        "Arizona": "AZ",
        "Arkansas": "AR",
        "California": "CA",
        "Colorado": "CO",
        "Connecticut": "CT",
        "Delaware": "DE",
        "Florida": "FL",
        "Georgia": "GA",
        "Hawaii": "HI",
        "Idaho": "ID",
        "Illinois": "IL",
        "Indiana": "IN",
        "Iowa": "IA",
        "Kansas": "KS",
        "Kentucky": "KY",
        "Louisiana": "LA",
        "Maine": "ME",
        "Maryland": "MD",
        "Massachusetts": "MA",
        "Michigan": "MI",
        "Minnesota": "MN",
        "Mississippi": "MS",
        "Missouri": "MO",
        "Montana": "MT",
        "Nebraska": "NE",
        "Nevada": "NV",
        "New Hampshire": "NH",
        "New Jersey": "NJ",
        "New Mexico": "NM",
        "New York": "NY",
        "North Carolina": "NC",
        "North Dakota": "ND",
        "Ohio": "OH",
        "Oklahoma": "OK",
        "Oregon": "OR",
        "Pennsylvania": "PA",
        "Rhode Island": "RI",
        "South Carolina": "SC",
        "South Dakota": "SD",
        "Tennessee": "TN",
        "Texas": "TX",
        "Utah": "UT",
        "Vermont": "VT",
        "Virginia": "VA",
        "Washington": "WA",
        "West Virginia": "WV",
        "Wisconsin": "WI",
        "Wyoming": "WY",
        "District of Columbia": "DC"
        } 
        # invert the dictionary
        abbrev_to_us_state = dict(map(reversed, us_state_to_abbrev.items()))
        years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, None]
        for x in years:
            self.getStateQueryData(state, x)
        state = State(name=abbrev_to_us_state.get(state), twolettercode=state, summary=self.summaryjson, map=self.extractGeoJson(state), transformation=self.getTransformation(state))
        state.save()

    def getStateQueryData(self, state, year):
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
        self.summaryjson[year] = {
            "Sum_Payments": SumPaymentJson,
            "Top_Doctors": TopDoctorsJson,
            "Most_Common_Items": MostCommonDrugsJson,
            "Top_Items": TopItemPaymentsJson,
            "Top_Manufacturers": TopManufacturersJson,
            }

    def getOpioidSummary(self, state, year):
        state = state.twolettercode
        if year:
            transactions = Transaction.objects.filter(Doctor__State = state, Date__year=year, OpioidInvolved=True).prefetch_related("transactionitems").select_related("Manufacturer")
        else:
            transactions = Transaction.objects.filter(Doctor__State = state, OpioidInvolved=True).prefetch_related("transactionitems").select_related("Manufacturer")
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
        self.summaryOpioidJson[year] = {
            "Sum_Payments": SumPaymentJson,
            "Top_Doctors": TopDoctorsJson,
            "Most_Common_Items": MostCommonDrugsJson,
            "Top_Items": TopItemPaymentsJson,
            "Top_Manufacturers": TopManufacturersJson,
            }
        
    def extractGeoJson(self, state):
        with open("healthdata/data/statemaps/{}.geojson".format(state),"r") as file:
            data = json.load(file)
            return data

    def getTransformation(self, state):
        with open("healthdata/data/StateTransformations.json","r") as file:
            data = json.load(file)
            data = data[state]
            return data

    def opioidSummary(self):
        states = State.objects.all()
        years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, None]
        with alive_bar(states.count()) as bar:
            for state in states:
                for year in years:
                    self.getOpioidSummary(state, year)
                state.summary["OpioidSummary"] = self.summaryOpioidJson
                state.save()

    def getRankings(self):
        states = State.objects.all().annotate(
                sum_pay=RawSQL("summary #> '{All}' #> '{Sum_Payments}'", [])
            ).annotate(
                sum_pay=RawSQL("summary #> '{All}' #> '{Sum_Payments}'", [])
            )
        states = states.annotate(pay_rank=Window(
                expression=Rank(),
                order_by=F('sum_pay').desc()
            ),
        )
        for state in states:
            print(state.rank)

    def handle(self, *args, **kwargs):
        print("Begin script")
        self.opioidSummary()
                
            
        