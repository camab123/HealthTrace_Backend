from typing import ItemsView
from django.urls import path
from rest_framework.routers import SimpleRouter

# from .views import DoctorSummary, DoctorsViewSet, ManufacturersViewSet, TransactionsViewSet
from .views import StateRank, StateOpioidSummary, StateMapData, StateSummaryData, DoctorList, DoctorListDetail, DoctorDetail, DoctorSummary, ManufacturersList, ManufacturerDetail, ManufacturerSummary, TransactionList

urlpatterns = [
    path('doctor/<str:doctorid>/', DoctorDetail.as_view(), name="DoctorDetail"),
    path('doctorsearch/', DoctorList.as_view(), name="DoctorList"),
    path('doctors/', DoctorListDetail.as_view(), name="DoctorListDetail"),
    path('statemap/<str:name>/', StateMapData.as_view(), name="StateMap"),
    path('statesummary/<str:name>/', StateSummaryData.as_view(), name="StateSummary"),
    path('statesummaryopioids/<str:name>/', StateOpioidSummary.as_view(), name="StateOpioidSummary"),
    path('stateranking/<str:name>/', StateRank.as_view(), name="StateRanking"),
    path('doctorsummary/<str:doctorid>/', DoctorSummary.as_view(), name="DoctorSummary"),
    path('manufacturers/', ManufacturersList.as_view(), name="ManufacturerList"),
    path('manufacturers/<str:manufacturerid>/', ManufacturerDetail.as_view(), name="ManufacturerDetail"),
    path('manufacturersummary/<str:manufacturerid>/', ManufacturerSummary.as_view(), name="ManufacturerSummary"),
    path('transactions/', TransactionList.as_view(), name="TransactionList"),
]