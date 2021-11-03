from django.db.models.aggregates import Max
from rest_framework import serializers, viewsets, filters
from rest_framework.views import APIView

from healthdata.serializers import DoctorSerializer, ManufacturerSerializer, TransactionSerializer, DoctorSummarySerializer, TransactionsForSummarySerializer
from .models import Doctor, Manufacturer, Transaction
from .permissions import IsStafforReadOnly
from rest_framework.response import Response
from django.core.paginator import Paginator
from rest_framework.decorators import api_view

from django.http import Http404
from django.db.models import Count, Sum, query
import time

from django.forms.models import model_to_dict

class DoctorDetail(APIView):
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, doctorid, format=None):
        doctor = Doctor.objects.get(pk=doctorid)
        serialized = doctor.serialize_doc()
        return Response(serialized, status=200)

class DoctorList(APIView):
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, format=None):
        search = self.request.query_params.get('search')
        page_number = self.request.query_params.get("page", 1)
        if search:
            terms = search.split()
            if len(terms) > 1:
                firstname = terms[0]
                lastname = terms[1]
                print(lastname)
                queryset = Doctor.objects.filter(LastName__iexact=lastname, FirstName__iexact=firstname)
            else:
                lastname = terms[0]
                queryset = Doctor.objects.filter(LastName__iexact=lastname)
        else:
            queryset = Doctor.objects.all()
        paginator = Paginator(queryset , 25)
        serializer = DoctorSerializer(paginator.page(page_number), many=True,  context={'request':request})
        return Response(serializer.data, status=200)

class DoctorSummary(APIView):
    permission_classes = (IsStafforReadOnly,)
    #filter_backends = (filters.SearchFilter,)
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
        top_manufacturers = transactions.values("Manufacturer__Name", "Manufacturer__ManufacturerId").annotate(top_manu=Count("Manufacturer__Name")).order_by("-top_manu")[:3]
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
    def get(self, request, manufacturerid, format=None):
        year = self.request.query_params.get('year')
        manufacturer = Manufacturer.objects.get(pk=manufacturerid)
        serialized = manufacturer.serialize_manu()
        if year and len(year) <= 4:
            transactions = manufacturer.manufacturerTransactions.filter(Date__year=year)
        else:
            transactions = manufacturer.manufacturerTransactions.prefetch_related("transactionitems").all()
        sum_payment = transactions.aggregate(Sum("Pay_Amount"))
        top_item_payments = transactions.exclude(transactionitems__Name__isnull=True).values("transactionitems__Type_Product", "transactionitems__Name").annotate(total=Sum('Pay_Amount')).order_by("-total")[:10]
        top_states = transactions.values("Doctor__State").annotate(top_states=Sum('Pay_Amount')).order_by("-top_states")[:10]
        top_doctors = transactions.values("Doctor__DoctorId", "Doctor__FirstName", "Doctor__MiddleName", "Doctor__LastName").annotate(top_docs=Count("Doctor__DoctorId")).order_by("-top_docs")[:3]
        largest_payoffs = transactions.values("Pay_Amount").annotate(top_pay=Max("Pay_Amount")).order_by("-top_pay")[:3]
        Most_Common_Drugs = transactions.values("transactionitems__Name", "transactionitems__Type_Product").annotate(top_drugs=Count("transactionitems__Name")).order_by("-top_drugs")[:3]
        data = {
            "ManufacturerDetails": serialized,
            "Sum_Payments": sum_payment,
            "Top_Doctors": top_doctors,
            "Largest_Payments": largest_payoffs,
            "Most_Common_Items": Most_Common_Drugs,
            "Top_Items": top_item_payments,
            "Top_States": top_states,
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
            queryset = Transaction.objects.filter(TransactionId__icontains=search).prefetch_related("transactionitems")
        else:
            queryset = Transaction.objects.all().prefetch_related("transactionitems")
        paginator = Paginator(queryset , 25)
        serializer = TransactionSerializer(paginator.page(page_number), many=True,  context={'request':request})
        print("Page took {} to load".format(time.time() - start))
        return Response(serializer.data, status=200)





