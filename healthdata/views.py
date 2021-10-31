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

class DoctorList(APIView):
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


class ManufacturersList(APIView):
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

class TransactionList(APIView):
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)
    def get(self, request, format=None):
        start = time.time()
        search = self.request.query_params.get('search')
        page_number = self.request.query_params.get("page", 1)
        if search:
            #queryset = Transaction.objects.filter(Doctor__DoctorId__icontains=search)
            queryset = Transaction.objects.filter(TransactionId__icontains=search)
        else:
            queryset = Transaction.objects.all()
        paginator = Paginator(queryset , 25)
        serializer = TransactionSerializer(paginator.page(page_number), many=True,  context={'request':request})
        print("Page took {} to load".format(time.time() - start))
        return Response(serializer.data, status=200)

class DoctorSummary(APIView):
    permission_classes = (IsStafforReadOnly,)
    #filter_backends = (filters.SearchFilter,)
    def get(self, request, search, format=None):
        # search = self.request.query_params.get('search')
        # queryset = Transaction.objects.filter(Doctor__DoctorId=search).select_related("Doctor")
        # queryset = queryset.prefetch_related("transactionitems")
        doctordata = Doctor.objects.get(pk=search)
        #transactions = doctordata.transactions.all()
        transactions = doctordata.transactions.all()
        transactionitems = transactions.prefetch_related("transactionitems")
        start = time.time()
        DoctorData = doctordata.serialize_doc()
        print(time.time() - start)
        #sum_payment = queryset.aggregate(Sum("Pay_Amount"))
        start = time.time()
        serialized = [e.serialize_summary() for e in transactionitems]
        print(time.time() - start)
        
        data = {
            "Doctor": DoctorData,
            "Transactions": serialized,
            #"Sum_Payment": sum_payment
        }
        return Response(data, status=200)



