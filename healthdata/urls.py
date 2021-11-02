from typing import ItemsView
from django.urls import path
from rest_framework.routers import SimpleRouter

# from .views import DoctorSummary, DoctorsViewSet, ManufacturersViewSet, TransactionsViewSet
from .views import DoctorList, DoctorDetail, DoctorSummary, ManufacturersList, TransactionList

urlpatterns = [
    path('doctor/<str:doctorid>/', DoctorDetail.as_view(), name="DoctorDetail"),
    path('doctors/', DoctorList.as_view(), name="DoctorList"),
    path('manufacturers/', ManufacturersList.as_view(), name="ManufacturerList"),
    path('transactions/', TransactionList.as_view(), name="TransactionList"),
    path('doctorsummary/<str:doctorid>/', DoctorSummary.as_view(), name="DoctorSummary"),
]