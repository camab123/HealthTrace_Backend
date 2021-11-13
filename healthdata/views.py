from django.db.models.aggregates import Max
from django.db.models import Count, Sum, query, Prefetch
from rest_framework import generics
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from healthdata.serializers import DoctorSerializer, ManufacturerSerializer, TransactionSerializer, DoctorSummarySerializer, TransactionsForSummarySerializer
from .models import Doctor, Manufacturer, Transaction, TransactionItem
from .permissions import IsStafforReadOnly

from django.core.paginator import Paginator
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from django.http import Http404

import time
import pandas as pd

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

class DoctorDetail(APIView):
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, doctorid, format=None):
        doctor = Doctor.objects.get(pk=doctorid)
        serialized = doctor.serialize_doc()
        return Response(serialized, status=200)

class DoctorList(generics.ListCreateAPIView):
    permission_classes = (IsStafforReadOnly,)
    search_fields = ['=LastName', "=FirstName"]
    filter_backends = (filters.SearchFilter,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class DoctorSummary(APIView):
    permission_classes = (IsStafforReadOnly,)
    # @method_decorator(cache_page(CACHE_TTL))
    def get(self, request, doctorid, format=None):
        year = self.request.query_params.get('year')
        doctordata = Doctor.objects.get(pk=doctorid)
        if year and len(year) <= 4:
            transactions = doctordata.transactions.select_related().filter(Date__year=year)
        else:
            transactions = doctordata.transactions.select_related().all()
        transactionitems = transactions.prefetch_related("transactionitems")
        doctor_serialized = doctordata.serialize_doc()
        serialized = [e.serialize_summary() for e in transactionitems]
        sum_payment = transactions.aggregate(Sum("Pay_Amount"))
        #Carelink: 345.18
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
        options = ["2016", "2017", "2018", "2019", "2020", "All", "all"]
        if year not in options or year is None:
            year = "All"
        manufacturer = Manufacturer.objects.get(pk=manufacturerid)
        serialized = manufacturer.serialize_manu()
        data = {
            "ManufacturerDetails": serialized,
            "SummaryData": manufacturer.SummaryData[year]
        }
        return Response(data, status=200)


# class ManufacturerSummary(APIView):
#     permission_classes = (IsStafforReadOnly,)
#     # @method_decorator(cache_page(CACHE_TTL))
#     def get(self, request, manufacturerid, format=None):
#         year = self.request.query_params.get('year')
#         manufacturer = Manufacturer.objects.get(pk=manufacturerid)
#         transactions = manufacturer.manufacturerTransactions.all().prefetch_related("transactionitems")
#         transactionids = TransactionItem.objects.filter(transactionitems__Manufacturer=manufacturer).values_list("id", flat=True)
#         transactionids = list(transactionids)
#         serialized = manufacturer.serialize_manu()
#         if year and len(year) <= 4:
#             TransactionQuerySet = transactions.filter(Date__year=year)
#         else:
#             TransactionQuerySet = transactions
#         SumPayment = TransactionQuerySet.aggregate(Sum("Pay_Amount"))
#         TopStates = TransactionQuerySet.values("Doctor__State").annotate(top_states=Sum("Pay_Amount")).order_by("-top_states")[:10]
#         TopDoctors = TransactionQuerySet.values("Doctor__DoctorId", "Doctor__FirstName", "Doctor__MiddleName", "Doctor__LastName").annotate(top_docs=Count("Doctor__DoctorId")).order_by("-top_docs")[:3]
#         LargestPayoffs = TransactionQuerySet.values("Pay_Amount").annotate(top_pay=Max("Pay_Amount")).order_by("-top_pay")[:3]
#         transactionitemsquery = TransactionItem.objects.exclude(Name__isnull=True).filter(id__in=transactionids).values("Type_Product", "Name")
#         MostCommonDrugs = transactionitemsquery.annotate(top_drugs=Count('Name')).order_by('-top_drugs')[:3]
#         TopItemPayments = transactionitemsquery.annotate(total=Sum('transactionitems__Pay_Amount')).order_by('-total')[:10]
#         data = {
#             "ManufacturerDetails": serialized,
#             "Sum_Payments": SumPayment,
#             "Top_Doctors": TopDoctors,
#             "Largest_Payments": LargestPayoffs,
#             "Most_Common_Items": MostCommonDrugs,
#             "Top_Items": TopItemPayments,
#             "Top_States": TopStates,
#         }
#         return Response(data, status=200)

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





