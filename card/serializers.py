from rest_framework import serializers


class IamportCallbackSerializer(serializers.Serializer):
    imp_uid = serializers.CharField()  # String
    merchant_uid = serializers.UUIDField()  # String
    paid_amount = serializers.IntegerField()  # Number
    apply_num = serializers.CharField()  # String


class BootpayCallbackSerializer(serializers.Serializer):
    receipt_id = serializers.CharField()  # String
    order_id = serializers.UUIDField()  # String
    price = serializers.IntegerField()  # Number
