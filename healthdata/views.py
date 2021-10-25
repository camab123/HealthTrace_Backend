from rest_framework import viewsets, filters
from .models import Doctor, Manufacturer, Transaction
from .permissions import IsStafforReadOnly
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import Http404
from django.db.models import Count, Sum

# Create your views here.
# class DoctorsViewSet(viewsets.ModelViewSet):
#     search_fields = ['FirstName', 'LastName']
#     permission_classes = (IsStafforReadOnly,)
#     filter_backends = (filters.SearchFilter,)
#     queryset = Doctor.objects.all()
#     serializer_class = DoctorSerializer

# class ManufacturersViewSet(viewsets.ModelViewSet):
#     permission_classes = (IsStafforReadOnly,)
#     filter_backends = (filters.SearchFilter,)
#     queryset = Manufacturer.objects.all()
#     serializer_class = ManufacturerSerializer

# class TransactionsViewSet(viewsets.ModelViewSet):
#     search_fields = ['Doctor__DoctorId']
#     permission_classes = (IsStafforReadOnly,)
#     filter_backends = (filters.SearchFilter,)
#     queryset = Transaction.objects.all()
#     serializer_class = TransactionSerializer

# class DoctorSummary(viewsets.ModelViewSet):
#     permission_classes = (IsStafforReadOnly,)
#     queryset = Doctor.objects.all()
#     serializer_class = DoctorSummarySerializer

class DoctorList(generics.GenericAPIView):
    queryset = Doctor.objects.all()
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            terms = search.split()
            if len(terms) > 1:
                firstname = terms[0]
                lastname = terms[1]
                print(lastname)
                return Doctor.objects.filter(LastName__iexact=lastname, FirstName__iexact=firstname)
            else:
                lastname = terms[0]
                return Doctor.objects.filter(LastName__iexact=lastname)
        else:
            return Doctor.objects.all()

    def get(self, request, format=None):
        search = self.request.query_params.get('search')
        queryset = self.get_queryset()
        page = self.request.query_params.get('page')
        if page is not None:
            paginate_queryset = self.paginate_queryset(queryset)
            serialized = [e.serialize() for e in paginate_queryset]
            return self.get_paginated_response(serialized)
        else:
            page = 1
            paginate_queryset = self.paginate_queryset(queryset)
            serialized = [e.serialize() for e in paginate_queryset]
            return self.get_paginated_response(serialized)

class ManufacturersList(generics.GenericAPIView):
    queryset = Manufacturer.objects.all()
    search_fields = ['Name']
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search')
        print(search)

        if search:
            return Manufacturer.objects.filter(Name__icontains=search)
        else:
            return Manufacturer.objects.all()

    def get(self, request, format=None):
        queryset = self.get_queryset()
        page = self.request.query_params.get('page')
        if page is not None:
            paginate_queryset = self.paginate_queryset(queryset)
            serialized = [e.serialize() for e in paginate_queryset]
            return self.get_paginated_response(serialized)
        else:
            page = 1
            paginate_queryset = self.paginate_queryset(queryset)
            serialized = [e.serialize() for e in paginate_queryset]
            return self.get_paginated_response(serialized)

class TransactionList(generics.GenericAPIView):
    queryset = Transaction.objects.all()
    search_fields = ['Doctor__DoctorId']
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            return Transaction.objects.filter(Doctor__DoctorId__icontains=search)
        else:
            return Transaction.objects.all()

    def get(self, request, format=None):
        search = self.request.query_params.get('search')
        queryset = self.get_queryset()
        page = self.request.query_params.get('page')
        if page is not None:
            paginate_queryset = self.paginate_queryset(queryset)
            serialized = [e.serialize() for e in paginate_queryset]
            return self.get_paginated_response(serialized)
        else:
            page = 1
            paginate_queryset = self.paginate_queryset(queryset)
            serialized = [e.serialize() for e in paginate_queryset]
            return self.get_paginated_response(serialized)

class DoctorSummary(generics.GenericAPIView):
    queryset = Transaction.objects.all()
    search_fields = ['Doctor__DoctorId']
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)
    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            return Transaction.objects.filter(Doctor__DoctorId=search).order_by("-Date")
        else:
            raise Http404

    def get(self, request, format=None):
        search = self.request.query_params.get('search')
        queryset = self.get_queryset()
        serialized = [e.serialize() for e in queryset]
        sum_payments = 0
        sum_payments = queryset.aggregate(Sum('Pay_Amount'))
        doctor_info = Doctor.objects.filter(pk=search)
        doctor_serialized = [e.serialize() for e in doctor_info]
        most_common_drugs = queryset.values("Name").annotate(count=Count('Name')).order_by("-count")
        most_common_companies = queryset.values("Manufacturer__Name").annotate(count=Count('Manufacturer')).order_by("-count")
        largest_pay_list = queryset.values("Pay_Amount").order_by("-Pay_Amount")
        data = {
            "Doctor_Info": doctor_serialized[0],
            "Drug_List": most_common_drugs[:5],
            "Manufacturer_List": most_common_companies[:5],
            "Largest_Payments": largest_pay_list[:5],
            "Sum_Payments": sum_payments,
            "Latest_Transactions": serialized[:5]
        }
        return Response(data)

