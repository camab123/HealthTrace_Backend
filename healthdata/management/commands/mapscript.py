from os import stat
from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from pandas.core.indexes.base import Index
from datetime import datetime  
from tqdm import tqdm
import json

from healthdata.models import Transaction
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

    def handle(self, *args, **kwargs):
        print("Begin script")
        self.GenerateStylingNulls()