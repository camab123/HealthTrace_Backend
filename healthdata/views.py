from django.db.models.aggregates import Max
from django.db.models import Count, Sum
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from healthdata.serializers import DoctorSerializer, ManufacturerSerializer, TransactionSerializer, DoctorSummarySerializer, TransactionsForSummarySerializer
from .models import Doctor, Manufacturer, Transaction
from .permissions import IsStafforReadOnly
from django.core.paginator import Paginator
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import time
import pandas as pd
from django.db.models import F, Value
from django.db.models.functions import Concat

from django.contrib.postgres.search import SearchVector, SearchRank

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

class DoctorDetail(APIView):
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, doctorid, format=None):
        doctor = Doctor.objects.get(pk=doctorid)
        serialized = doctor.serialize_doc()
        return Response(serialized, status=200)

class DoctorListDetail(APIView):
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, format=None):
        search = self.request.query_params.get('search')
        page_number = self.request.query_params.get("page", 1)
        startlim = (int(page_number) * 25) - 25
        endlim = (int(page_number) * 25)
        queryset = Doctor.objects.all().order_by("LastName", "DoctorId").values("DoctorId", "FirstName", "MiddleName", "LastName", "StreetAddress1", "StreetAddress2", "City", "State")
        if search:
            search = search.split(" ")
            if len(search) > 1:
                queryset = queryset.filter(FirstName__istartswith=search[0]).filter(LastName__istartswith=search[1])
            else:
                queryset = queryset.filter(LastName__istartswith=search[0])
        pagecount = round(len(queryset)/25) + 1
        serializer = [e for e in queryset[startlim:endlim]]
        return Response({"Doctors": serializer, "Pages": pagecount}, status=200)

class DoctorList(APIView):
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, format=None):
        search = self.request.query_params.get('search')
        query_terms = search.split()
        tsquery = " & ".join(query_terms)
        tsquery += ":*"
        doctorqueryset = Doctor.objects.all().values("DoctorId", "FirstName", "MiddleName", "LastName")
        manufacturerqueryset = Manufacturer.objects.all().values("ManufacturerId", "Name")
        if search:
            doctorqueryset = Doctor.objects.extra(where=["doctor_name_idx @@ (to_tsquery(%s)) = true"],params=[tsquery]).values('DoctorId', 'FirstName', "MiddleName", "LastName")
            manufacturerqueryset = manufacturerqueryset.filter(Name__istartswith=search)
        doctorserialized = [e for e in doctorqueryset[:5]]
        manufacturerserialized = [e for e in manufacturerqueryset[:5]]
        data = {"Doctors": doctorserialized, "Manufacturers": manufacturerserialized}
        return Response(data, status=200)

class DoctorSummary(APIView):
    permission_classes = (IsStafforReadOnly,)
    # @method_decorator(cache_page(CACHE_TTL))
    def get(self, request, doctorid, format=None):
        year = self.request.query_params.get('year')
        doctordata = Doctor.objects.get(pk=doctorid)
        if year:
            transactions = doctordata.transactions.select_related("Manufacturer").filter(Date__year=year)
        else:
            transactions = doctordata.transactions.select_related("Manufacturer").only("Pay_Amount", "Date", "Payment", "Nature_Payment", "Contextual_Info", "Manufacturer__Name", "Manufacturer__ManufacturerId", "transactionitems", "Doctor__DoctorId")
        transactionitems = transactions.prefetch_related("transactionitems")
        doctor_serialized = doctordata.serialize_doc()
        serialized = [e.serialize_summary() for e in transactionitems]
        sum_payment = transactions.aggregate(Sum("Pay_Amount"))
        top_item_payments = transactionitems.exclude(transactionitems__Name__isnull=True).values("transactionitems__Type_Product", "transactionitems__Name").annotate(total=Sum('Pay_Amount')).order_by("-total")[:5]
        top_manufacturers = transactions.values("Manufacturer__Name", "Manufacturer__ManufacturerId").annotate(top_manu=Count("Manufacturer__Name")).order_by("-top_manu")[:8]
        largest_payoffs = transactions.values("Pay_Amount").annotate(top_pay=Max("Pay_Amount")).order_by("-top_pay")[:3]
        Most_Common_Drugs = transactionitems.values("transactionitems__Name", "transactionitems__Type_Product").annotate(top_drugs=Count("transactionitems__Name")).order_by("-top_drugs")[:3]
        data = {
            "Doctor": doctor_serialized,
            "Top_Manufacturers": top_manufacturers,
            "Top_Payment": largest_payoffs,
            "Top_Drugs": Most_Common_Drugs,
            "Top_Paid_Items": top_item_payments,
            "Transactions": serialized,
            "Sum_Payment": sum_payment
        }
        return Response(data, status=200)

class ManufacturersList(APIView):
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, format=None):
        search = self.request.query_params.get('search')
        page_number = self.request.query_params.get("page", 1)
        if search:
            queryset = Manufacturer.objects.filter(Name__icontains=search)
        else:
            queryset = Manufacturer.objects.all()
        paginator = Paginator(queryset , 25)
        serializer = ManufacturerSerializer(paginator.page(page_number), many=True,  context={'request':request})
        return Response(serializer.data, status=200)

class ManufacturerDetail(APIView):
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, manufacturerid, format=None):
        year = self.request.query_params.get('year')
        manufacturer = Manufacturer.objects.get(pk=manufacturerid)
        serialized = manufacturer.serialize_manu()
        return Response(serialized, status=200)

class ManufacturerSummary(APIView):
    permission_classes = (IsStafforReadOnly,)
    # @method_decorator(cache_page(CACHE_TTL))
    def get(self, request, manufacturerid, format=None):
        year = self.request.query_params.get('year')
        manufacturer = Manufacturer.objects.get(pk=manufacturerid)
        keys = manufacturer.SummaryData.keys()
        if year not in keys or year is None:
            year = "All"
        serialized = manufacturer.serialize_manu()
        data = {
            "ManufacturerDetails": serialized,
            "Summary Data": manufacturer.SummaryData[year]
        }
        return Response(data, status=200)

class TransactionList(APIView):
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)
    def get(self, request, format=None):
        start = time.time()
        search = self.request.query_params.get('search')
        page_number = self.request.query_params.get("page", 1)
        if search:
            queryset = Transaction.objects.filter(TransactionId=search).prefetch_related("transactionitems")
        else:
            queryset = Transaction.objects.all().prefetch_related("transactionitems")
        paginator = Paginator(queryset , 25)
        serializer = TransactionSerializer(paginator.page(page_number), many=True,  context={'request':request})
        print("Page took {} to load".format(time.time() - start))
        return Response(serializer.data, status=200)





