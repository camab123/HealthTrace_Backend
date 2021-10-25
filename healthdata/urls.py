from typing import ItemsView
from django.urls import path
from rest_framework.routers import SimpleRouter

# from .views import DoctorSummary, DoctorsViewSet, ManufacturersViewSet, TransactionsViewSet
from .views import DoctorList, DoctorSummary, ManufacturersList, TransactionList
# router = SimpleRouter()
# router.register('doctors', DoctorsViewSet, basename="doctors")
# router.register('manufacturers', ManufacturersViewSet, basename="manufacturers")
# router.register('transactions', TransactionsViewSet, basename="transactions")
# router.register('doctorsummary', DoctorSummary, basename="doctorsummer")
# urlpatterns = router.urls

urlpatterns = [
    path('doctors/', DoctorList.as_view(), name="DoctorList"),
    path('manufacturers/', ManufacturersList.as_view(), name="ManufacturerList"),
    path('transactions/', TransactionList.as_view(), name="TransactionList"),
    path('doctorsummary/', DoctorSummary.as_view(), name="DoctorSummary"),
]