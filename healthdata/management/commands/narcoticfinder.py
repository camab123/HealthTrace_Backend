from django.core.management.base import BaseCommand, CommandError
import csv
import pandas as pd
from pandas.core.indexes.base import Index
import requests
from datetime import datetime  
from tqdm import tqdm
import time
from django.db.models import Sum, Count
from healthdata.models import Doctor, Manufacturer, Transaction, TransactionItem
from bs4 import BeautifulSoup
tqdm.pandas()

class Command(BaseCommand):
    def __init__(self):
        self.narcoticsList = [
            "OxyContin",
            "Roxicodone",
            "Oxecta",
            "Oxaydo",
            "Xtampza",
            "Percodan",
            "Targiniq",
            "Xartemis",
            "Oxycet",
            "Roxicet",
            "Tylox",
            "Percocet",
            "Oxycodone",
            "Hydrocodone-Acetaminophen",
            "Vicodin",
            "Norco",
            "Lorcet",
            "Zamicet",
            "Verdrocet",
            "Lortab",
            "Anexsia",
            "Co-Gesic",
            "Hycet",
            "Liquicet",
            "Maxidone",
            "Norco",
            "Xodol",
            "Zolvit",
            "Zydone",
            "Hydrocodone",
            "Sysingla",
            "Zohydro",
            "Hydrocodone-Homatropine",
            "Hycodan",
            "Hydromet",
            "Hyrdocodone",
            "Ibudone",
            "Xylon",
            "Reprexain",
            "Vicoprofen",
            "Pseudoephedrine-Hydrocodone",
            "Rezira",
            "Hydrocodone-Clorpheniramine",
            "Vituz",
            "Hydrocodone-Cpm-Pseudoephed",
            "Zutripro",
            "Morphine",
            "Duramorph",
            "Infumorph",
            "MS Contin",
            "Oramorph",
            "Avinza",
            "Arymo",
            "Kadian",
            "Morphabond",
            "Roxanol-T",
            "Morphine-Naltrexone",
            "Embeda",
            "Hydromorphone",
            "Dilaudid",
            "Exalgo",
            "Palladone",
            "Fentanyl",
            "Actiq",
            "Fentora",
            "Abstral",
            "Lazanda",
            "Onsolis",
            "Sublimaze",
            "Fentanyl",
            "Duragesic",
            "Subsys",
            "Codeine Poli-Chlorphenir Poli",
            "Tuzistra",
            "Acetaminophen with codeine phosphate/Acetaminophen-Codeine",
            "Methadone",
            "Dolophine",
            "Methadose",
            "Methadone",
            "Methadose",
            "Morphine",
            "Morphabond",
            "Oxymorphone",
            "Opana",
            "Demerol",
            "Meperidine",
            "Tramadol",
            "Carfentanil",
            "Buprenorphine",
            "Subatex",
            "Buprenex",
            "Butrans",
            "Probuphine",
            "hysingla",
            "nucynta",
            "morco",
            "tussiCaps",
            "tussionex",
            "tuzistra",
            "codeine",
            "hydrocodone",
            "tapentadol"
        ]
    def GetTransactionItems(self):
        transactionitems = TransactionItem.objects.all().exclude(Type_Product="Device")
        transactionitems.update(Opioid=False)
        counter = 0
        for x in transactionitems.values():
            name = x["Name"].lower()
            for val in self.narcoticsList:
                if val.lower() in name:
                    counter = counter + 1
                    drug = TransactionItem.objects.get(id=x["id"])
                    drug.Opioid = True
                    drug.save()
                    break
    def AddOpioidInvolvement(self):
        opioidtransactions = TransactionItem.objects.filter(Opioid=True)
        Transactions = Transaction.objects.filter(transactionitems__in=opioidtransactions)
        Transactions.update(OpioidInvolved=True)

    def GetAllOpioidTransactions(self):
        Transactions = Transaction.objects.filter(OpioidInvolved=True)
        SumNarcotics = Transactions.aggregate(NarcoticSum=Sum("Pay_Amount"))
        TopStates = Transactions.values("Doctor__State").annotate(top_states=Sum("Pay_Amount")).order_by("-top_states")[:10]
        TopDoctors = Transactions.values("Doctor__DoctorId", "Doctor__FirstName", "Doctor__MiddleName", "Doctor__LastName").annotate(top_docs=Count("Doctor__DoctorId")).order_by("-top_docs")[:10]
        TopManufacturers = Transactions.values("Manufacturer__ManufacturerId", "Manufacturer__Name").annotate(Top_Manufacturers=Sum("Pay_Amount")).order_by("-Top_Manufacturers")[:10]
        print("TOP DOCTORS: {}".format(TopDoctors))
        print("TOP STATES: {}".format(TopStates))
        print("TOP MANUFACTURERS: {}".format(TopManufacturers))
        print("SUM PAYMENTS: {}".format(SumNarcotics))
    
    def getListofDrugs(self):
        url = "https://drugfree.org/drugs/prescription-pain-relievers-opioids/?utm_source=google&utm_medium=kp&utm_campaign=opioid"
        response = requests.get(url).text
        drugList = []
        soup = BeautifulSoup(response, "html.parser")
        table_data = soup.find("table")
        table_data = table_data.find_all("td")
        for x in table_data[2:]:
            x = x.text
            x = x.split()
            for drug in x:
                drug = drug.replace(",", "")
                drug = drug.replace("-", "")
                if drug != "—":
                    drugList.append(drug)
        drugList = drugList + self.narcoticsList
        drugList = list(set(drugList))
        self.narcoticsList = drugList

    def handle(self, *args, **kwargs):
        self.GetAllOpioidTransactions()
        