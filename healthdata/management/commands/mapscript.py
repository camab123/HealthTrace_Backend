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
from django.db import connection
from django.db.models.functions import Cast
from django.db.models import FloatField, ExpressionWrapper
from decimal import Decimal
import re
tqdm.pandas()

popdata = {'Alabama': 4903185.0, 'Alaska': 731545.0, 'Arizona': 7278717.0, 'Arkansas': 3017804.0, 'California': 39512223.0, 'Colorado': 5758736.0, 'Connecticut': 3565287.0, 'Delaware': 973764.0, 'District of Columbia': 705749.0, 'Florida': 21477737.0, 'Georgia': 10617423.0, 'Hawaii': 1415872.0, 'Idaho': 1787065.0, 'Illinois': 12671821.0, 'Indiana': 6732219.0, 'Iowa': 3155070.0, 'Kansas': 2913314.0, 'Kentucky': 4467673.0, 'Louisiana': 4648794.0, 'Maine': 1344212.0, 'Maryland': 6045680.0, 'Massachusetts': 6892503.0, 'Michigan': 9986857.0, 'Minnesota': 5639632.0, 'Mississippi': 2976149.0, 'Missouri': 6137428.0, 'Montana': 1068778.0, 'Nebraska': 1934408.0, 'Nevada': 3080156.0, 'New Hampshire': 1359711.0, 'New Jersey': 8882190.0, 'New Mexico': 2096829.0, 'New York': 19453561.0, 'North Carolina': 10488084.0, 'North Dakota': 762062.0, 'Ohio': 11689100.0, 'Oklahoma': 3956971.0, 'Oregon': 4217737.0, 'Pennsylvania': 12801989.0, 'Rhode Island': 1059361.0, 'South Carolina': 5148714.0, 'South Dakota': 884659.0, 'Tennessee': 6829174.0, 'Texas': 28995881.0, 'Utah': 3205958.0, 'Vermont': 623989.0, 'Virginia': 8535519.0, 'Washington': 7614893.0, 'West Virginia': 1792147.0, 'Wisconsin': 5822434.0, 'Wyoming': 578759.0}

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
            transactions = Transaction.objects.filter(Doctor__State=state, Date__year=year).prefetch_related("transactionitems").select_related("Manufacturer")
        else:
            transactions = Transaction.objects.filter(Doctor__State=state).prefetch_related("transactionitems").select_related("Manufacturer")
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
        states = State.objects.exclude(summary__has_key="OpioidSummary")
        years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, None]
        with alive_bar(states.count()) as bar:
            for state in states:
                lettercode = state.twolettercode
                print(lettercode)
                for year in years:
                    self.getOpioidSummary(lettercode, year)
                times = [float(x["time"]) for x in connection.queries]
                #Print out the top 10 longest queries
                print(lettercode, sorted(times, key = float, reverse=True)[:20])
                state.summary["OpioidSummary"] = self.summaryOpioidJson
                state.save()
                bar()

    def getRankings(self):
        states = State.objects.all()
        data = []
        for state in states:
            state.opioid_sum = state.summary["OpioidSummary"]["All"]["Sum_Payments"]
            state.sum_pay = state.summary["All"]["Sum_Payments"]
            data.append({
                "State": state.name,
                "Transaction": state.summary["All"]["Sum_Payments"],
                "Opioid_sum": state.summary["OpioidSummary"]["All"]["Sum_Payments"],
                "Transaction_Per_Capita" : state.summary["All"]["Sum_Payments"]/popdata.get(state.name),
                "Opioid_Per_Capita": state.summary["OpioidSummary"]["All"]["Sum_Payments"]/popdata.get(state.name)
            })
        df = pd.DataFrame(data)
        df["TransactionRankPerCapita"] = df["Transaction_Per_Capita"].rank(ascending=False).astype(int)
        df["OpioidRankPerCapita"] = df["Opioid_Per_Capita"].rank(ascending=False).astype(int)
        for index, row in df.iterrows():
            state = State.objects.filter(name=row["State"])[0]
            state.ranking = None
            state.ranking = {
                "Rank": row["TransactionRankPerCapita"],
                "OpioidRank": row["OpioidRankPerCapita"]
            }
            state.save()
    def handle(self, *args, **kwargs):
        print("Begin script")
        self.getRankings()
                
            
        