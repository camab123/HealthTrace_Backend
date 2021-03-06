from django.db.models.aggregates import Max
from django.db.models import Count, Sum
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response
from healthdata.serializers import ManufacturerSerializer, TransactionSerializer, TransactionsForSummarySerializer
from .models import Doctor, Manufacturer, Transaction, State
from .permissions import IsStafforReadOnly
from django.core.paginator import Paginator
from rest_framework.pagination import LimitOffsetPagination
from .paginations import TransactionSummaryPaginator
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from rest_framework.throttling import ScopedRateThrottle
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import time

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

class DoctorDetail(APIView):
    permission_classes = (IsStafforReadOnly,)
    throttle_scope = 'general'
    def get(self, request, doctorid, format=None):
        doctor = Doctor.objects.get(pk=doctorid)
        serialized = doctor.serialize_doc()
        return Response(serialized, status=200)

class DoctorSearch(APIView):
    permission_classes = (IsStafforReadOnly,)
    throttle_scope = 'search'
    def get(self, request, format=None):
        search = self.request.query_params.get('name')
        query_terms = search.split()
        tsquery = ":* & ".join(query_terms)
        tsquery += ":*"
        page_number = self.request.query_params.get("page", 1)
        startlim = (int(page_number) * 25) - 25
        endlim = (int(page_number) * 25)
        doctorqueryset = Doctor.objects.all().values("DoctorId", "FirstName", "MiddleName", "LastName", "StreetAddress1", "StreetAddress2", "City", "State")[:250]
        if search:
            doctorqueryset = Doctor.objects.extra(where=["doctor_name_idx @@ (to_tsquery(%s)) = true"],params=[tsquery]).values("DoctorId", "FirstName", "MiddleName", "LastName", "StreetAddress1", "StreetAddress2", "City", "State")[:250]
        pagecount = round(len(doctorqueryset)/25)
        doctorserialized = [e for e in doctorqueryset[startlim:endlim]]
        data = {"Doctors": doctorserialized, "Pages": pagecount}
        return Response(data, status=200)

class DoctorList(APIView):
    permission_classes = (IsStafforReadOnly,)
    throttle_scope = 'search'
    def get(self, request, format=None):
        search = self.request.query_params.get('search')
        query_terms = search.split()
        tsquery = " & ".join(query_terms)
        tsquery += ":*"
        doctorqueryset = Doctor.objects.all().values("DoctorId", "FirstName", "MiddleName", "LastName")
        manufacturerqueryset = Manufacturer.objects.all().values("ManufacturerId", "Name")
        if search:
            doctorqueryset = Doctor.objects.extra(where=["doctor_name_idx @@ (to_tsquery(%s)) = true"],params=[tsquery]).values('DoctorId', 'FirstName', "MiddleName", "LastName")[:250]
            manufacturerqueryset = manufacturerqueryset.filter(Name__istartswith=search)[:100]
        doctorserialized = [e for e in doctorqueryset[:5]]
        manufacturerserialized = [e for e in manufacturerqueryset[:5]]
        data = {"Doctors": doctorserialized, "Manufacturers": manufacturerserialized}
        return Response(data, status=200)

class DoctorSummary(APIView):
    throttle_scope = 'doctor'
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
        sum_payment = transactions.aggregate(Sum("Pay_Amount"))
        top_item_payments = transactionitems.exclude(transactionitems__Name__isnull=True).values("transactionitems__Type_Product", "transactionitems__Name").annotate(total=Sum('Pay_Amount')).order_by("-total")[:5]
        top_manufacturers = transactions.values("Manufacturer__Name", "Manufacturer__ManufacturerId").annotate(top_manu=Count("Manufacturer__Name")).order_by("-top_manu")[:8]
        largest_payoffs = transactions.values("Pay_Amount").annotate(top_pay=Max("Pay_Amount")).order_by("-top_pay")[:5]
        Most_Common_Drugs = transactionitems.values("transactionitems__Name", "transactionitems__Type_Product").annotate(top_drugs=Count("transactionitems__Name")).order_by("-top_drugs")[:5]
        data = {
            "Doctor": doctor_serialized,
            "Top_Manufacturers": top_manufacturers,
            "Top_Payment": largest_payoffs,
            "Top_Drugs": Most_Common_Drugs,
            "Top_Paid_Items": top_item_payments,
            "Sum_Payment": sum_payment
        }
        return Response(data, status=200)

class DoctorTransactions(APIView):
    permission_classes = (IsStafforReadOnly,)
    throttle_scope = 'doctor'
    # @method_decorator(cache_page(CACHE_TTL))
    def get(self, request, doctorid, format=None):
        year = self.request.query_params.get('year')
        page_number = self.request.query_params.get("page", 1)
        lim_count = 10
        startlim = (int(page_number) * lim_count) - lim_count
        endlim = (int(page_number) * lim_count)
        doctordata = Doctor.objects.get(pk=doctorid)
        if year:
            transactioncount = doctordata.transactions.filter(Date__year=year).count()
            transactions = doctordata.transactions.select_related("Manufacturer").filter(Date__year=year)[startlim:endlim]
        else:
            transactioncount = doctordata.transactions.count()
            transactions = doctordata.transactions.select_related("Manufacturer")[startlim:endlim]
        transactionitems = transactions.prefetch_related("transactionitems")
        pagecount = round((transactioncount)/lim_count)
        nextpage = int(page_number) + 1
        if nextpage > pagecount:
            nextpage = None
        serialized = [e.serialize_summary() for e in transactionitems.prefetch_related("transactionitems")]
        data = {
            "Transactions": serialized,
            "PageCount": pagecount,
            "nextPage": nextpage
        }
        return Response(data, status=200)

class StateRank(APIView):
    throttle_scope = 'general'
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, name, format=None):
        state = State.objects.get(twolettercode=name)
        data = {
            "Name": state.name,
            "Ranking": state.ranking,
        }
        return Response(data, status=200)

class StateMapData(APIView):
    throttle_scope = 'general'
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, name, format=None):
        state = State.objects.get(twolettercode=name)
        data = {
            "Name": state.name,
            "Map": state.map,
            "Transformation": state.transformation
        }
        return Response(data, status=200)

class StateSummaryData(APIView):
    throttle_scope = 'general'
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, name, format=None):
        year = self.request.query_params.get('year')
        years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, "All"]
        state = State.objects.get(twolettercode=name)
        keys = state.summary.keys()
        if year not in keys or year is None:
            year = "All"
        data = {
            "Name": state.name,
            "Summary": state.summary[year],
        }
        return Response(data, status=200)

class StateOpioidSummary(APIView):
    throttle_scope = 'general'
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, name, format=None):
        year = self.request.query_params.get('year')
        years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, "All"]
        state = State.objects.get(twolettercode=name)
        keys = state.summary.keys()
        if year not in keys or year is None:
            year = "All"
        data = {
            "Name": state.name,
            "Summary": state.summary["OpioidSummary"][year],
        }
        return Response(data, status=200)

class ManufacturersList(APIView):
    throttle_scope = 'general'
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
    throttle_scope = 'general'
    permission_classes = (IsStafforReadOnly,)
    def get(self, request, manufacturerid, format=None):
        year = self.request.query_params.get('year')
        manufacturer = Manufacturer.objects.get(pk=manufacturerid)
        serialized = manufacturer.serialize_manu()
        return Response(serialized, status=200)

class ManufacturerSummary(APIView):
    throttle_scope = 'general'
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
            # queryset = Transaction.objects.all().prefetch_related("transactionitems")
            return Response("Input a transactionid", status=404)
        paginator = Paginator(queryset , 25)
        serializer = TransactionSerializer(paginator.page(page_number), many=True,  context={'request':request})
        return Response(serializer.data, status=200)





