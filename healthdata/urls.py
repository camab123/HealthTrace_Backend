from typing import ItemsView
from django.urls import path
from rest_framework.routers import SimpleRouter

# from .views import DoctorSummary, DoctorsViewSet, ManufacturersViewSet, TransactionsViewSet
from .views import DoctorTransactions, DoctorSearch, StateRank, StateOpioidSummary, StateMapData, StateSummaryData, DoctorList, DoctorDetail, DoctorSummary, ManufacturersList, ManufacturerDetail, ManufacturerSummary, TransactionList

urlpatterns = [
    path('doctor/overview/<str:doctorid>/', DoctorDetail.as_view(), name="DoctorDetail"),
    path('doctor/search/', DoctorSearch.as_view(), name="DoctorSearch"),
    path('doctor/transactions/<str:doctorid>/', DoctorTransactions.as_view(), name="DoctorTransactions"),
    path('doctor/autofillsearch/', DoctorList.as_view(), name="DoctorList"),
    path('doctor/summary/<str:doctorid>/', DoctorSummary.as_view(), name="DoctorSummary"),

    path('state/map/<str:name>/', StateMapData.as_view(), name="StateMap"),
    path('state/summary/<str:name>/', StateSummaryData.as_view(), name="StateSummary"),
    path('state/summaryopioids/<str:name>', StateOpioidSummary.as_view(), name="StateOpioidSummary"),
    path('state/ranking/<str:name>/', StateRank.as_view(), name="StateRanking"),
    
    path('manufacturer/', ManufacturersList.as_view(), name="ManufacturerList"),
    path('manufacturer/overview/<str:manufacturerid>/', ManufacturerDetail.as_view(), name="ManufacturerDetail"),
    path('manufacturer/summary/<str:manufacturerid>/', ManufacturerSummary.as_view(), name="ManufacturerSummary"),

    path('transactions/', TransactionList.as_view(), name="TransactionList"),
]