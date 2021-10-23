from rest_framework import viewsets

from .models import Doctor, Manafacturer, Transaction

from .permissions import IsStafforReadOnly
from .serializers import DoctorSerializer, ManafacturerSerializer, TransactionSerializer

# Create your views here.
class DoctorsViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStafforReadOnly,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class ManafacturersViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStafforReadOnly,)
    queryset = Manafacturer.objects.all()
    serializer_class = ManafacturerSerializer

class TransactionsViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStafforReadOnly,)
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer