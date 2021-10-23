from rest_framework import serializers
from .models import Doctor, Manafacturer, Transaction

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("__all__")
        model = Doctor

class ManafacturerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("__all__")
        model = Manafacturer

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("__all__")
        model = Transaction