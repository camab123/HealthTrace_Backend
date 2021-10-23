from typing import ItemsView
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import DoctorsViewSet, ManufacturersViewSet, TransactionsViewSet

router = SimpleRouter()
router.register('doctors', DoctorsViewSet, basename="doctors")
router.register('manufacturers', ManufacturersViewSet, basename="manufacturers")
router.register('transactions', TransactionsViewSet, basename="transactions")

urlpatterns = router.urls