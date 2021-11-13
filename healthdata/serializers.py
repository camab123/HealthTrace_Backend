from collections import OrderedDict
from rest_framework import serializers
from .models import Doctor, Manufacturer, Transaction, TransactionItem

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("__all__")
        model = Doctor

class TransactionItemSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = TransactionItem

class TransactionSerializer(serializers.ModelSerializer):
    transactionitems = TransactionItemSerializer(many=True, read_only=True)
    class Meta:
        fields = "__all__"
        model = Transaction

class TransactionsForSummarySerializer(serializers.ModelSerializer):
    transactionitems = TransactionItemSerializer(many=True, read_only=True)
    class Meta:
        fields = ["transactionitems", "Pay_Amount", "Date", "Payment", "Nature_Payment", "Contextual_Info"]
        model = Transaction

class DoctorSummarySerializer(serializers.ModelSerializer):
    #payment_sum = serializers.DecimalField(max_digits=14, decimal_places=2)
    Doctor = DoctorSerializer(many=False, read_only=True)
    transactionitems = TransactionItemSerializer(many=True, read_only=True)
    class Meta:
        fields = "__all__"
        model = Transaction

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["ManufacturerId", "Name", "State", "Country"]
        model = Manufacturer
