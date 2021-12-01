from django.contrib import admin
from .models import Doctor, Manufacturer, Transaction, TransactionItem, State
# Register your models here.

admin.site.register(Doctor)
admin.site.register(Manufacturer)
admin.site.register(Transaction)
admin.site.register(TransactionItem)
admin.site.register(State)