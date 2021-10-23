from rest_framework import viewsets, filters

from .models import Doctor, Manufacturer, Transaction

from .permissions import IsStafforReadOnly
from .serializers import DoctorSerializer, ManufacturerSerializer, TransactionSerializer

# Create your views here.
class DoctorsViewSet(viewsets.ModelViewSet):
    search_fields = ['FirstName', 'LastName']
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class ManufacturersViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer

class TransactionsViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStafforReadOnly,)
    filter_backends = (filters.SearchFilter,)
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer