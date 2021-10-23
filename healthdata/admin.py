from django.contrib import admin
from .models import Doctor, Manafacturer, Transaction
# Register your models here.

admin.site.register(Doctor)
admin.site.register(Manafacturer)
admin.site.register(Transaction)