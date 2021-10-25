from rest_framework import serializers
from .models import Doctor, Manufacturer, Transaction

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("__all__")
        model = Doctor

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("__all__")
        model = Manufacturer

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("__all__")
        model = Transaction
