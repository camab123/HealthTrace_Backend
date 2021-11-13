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
tqdm.pandas()

class Command(BaseCommand):
    def __init__(self):
        self.narcotics = {
            "abstral": "fentanyl",
            "actiq": "fentanyl",
            "avinza": "morphine",
            "butrans": "buprenorphine",
            "demerol": "meperidine",
            "dilaudid": "hydromorphone",
            "dolophine": "methadone",
            "duragesic": "fentanyl",
            "fentora": "fentanyl",
            "hysingla": "hydrocodone",
            "methadose": "methadone",
            "morphabond": "morphine",
            "nucynta": "tapentadol",
            "onsolis": "fentanyl",
            "oramorph": "morphine",
            "oxaydo": "oxycodone",
            "roxanol-T": "morphine",
            "sublimaze": "fentanyl",
            "xtampza": "oxycodone",
            "zohydro": "hydrocodone",
            "anexsia": "hydrocodone",
            "co-Gesic": "hydrocodone",
            "embeda": "morphine",
            "exalgo": "hydromorphone",
            "hycet": "hydrocodone",
            "hycodan": "hydrocodone",
            "hydromet": "hydrocodone",
            "ibudone": "hydrocodone",
            "kadian": "morphine",
            "liquicet": "hydrocodone",
            "lorcet": "hydrocodone",
            "lortab": "hydrocodone",
            "maxidone": "hydrocodone",
            "mS contin": "morphine",
            "morco": "hydrocodone",
            "opana": "oxymorphone",
            "oxyContin" : "oxycodone",
            "oxycet": "oxycodone",
            "palladone": "hydromorphone",
            "percocet": "oxycodone",
            "percodan": "oxycodone",
            "reprexain": "hydrocodone",
            "rezira": "hydrocodone",
            "roxicet": "oxycodone",
            "targiniq": "oxycodone",
            "tussiCaps": "hydrocodone",
            "tussionex": "hydrocodone",
            "tuzistra": "codeine",
            "vicodin": "hydrocodone",
            "vicodin": "hydrocodone",
            "vicodin": "hydrocodone",
            "vicoprofen": "hydrocodone",
            "vituz": "hydrocodone",
            "xartemis": "oxycodone",
            "xodol": "hydrocodone",
            "zolvit": "hydrocodone",
            "zutripro": "hydrocodone",
            "zydone": "hydrocodone",
            "fentanyl": "fentanyl",
            "methadone": "methadone",
            "morphine": "morphine",
            "oxymorphone": "oxymorphone"
        }
    def GetTransactionItems(self):
        transactionitems = TransactionItem.objects.all().exclude(Type_Product="Device")
        transactionitems.update(Opioid=False)
        counter = 0
        for x in transactionitems.values():
            name = x["Name"].lower()
            for key, value in self.narcotics.items():
                if key.lower() in name or value.lower() in name:
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
        print("TOP STATE S: {}".format(TopStates))
        print("TOP MANUFACTURERS: {}".format(TopManufacturers))
        print("SUM PAYMENTS: {}".format(SumNarcotics))
    def handle(self, *args, **kwargs):
        self.GetAllOpioidTransactions()