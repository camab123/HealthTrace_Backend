from typing import ItemsView
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import DoctorsViewSet, ManafacturersViewSet, TransactionsViewSet

router = SimpleRouter()
router.register('doctors', DoctorsViewSet, basename="doctors")
router.register('manafacturers', ManafacturersViewSet, basename="manafacturers")
router.register('transactions', TransactionsViewSet, basename="transactions")

urlpatterns = router.urls