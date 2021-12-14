from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from pandas.core.indexes.base import Index
from datetime import datetime
from healthdata.models import Doctor, Manufacturer, Transaction, TransactionItem
from tqdm import tqdm

class Command(BaseCommand):

    def __init__(self):
        pass

    def handle(self, *args, **kwargs):
        print("Begin script")
        #64763640
        print(Transaction.objects.filter(Contextual_Info="nan").count())
        for x in Transaction.objects.filter(Contextual_Info="nan").iterator():
            x.Contextual_Info = None
            #print(x.Contextual_Info)
            #print(x.Type_Product, x.Category, x.Name)
            x.save()