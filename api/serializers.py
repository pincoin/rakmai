from rest_framework import serializers


class OrderPaymentSerializer(serializers.Serializer):
    account = serializers.IntegerField()
    received = serializers.CharField()
    name = serializers.CharField(allow_blank=True)
    method = serializers.CharField()
    amount = serializers.CharField()
    balance = serializers.CharField()


class NaverOrderPaymentSerializer(serializers.Serializer):
    customer = serializers.CharField()
    product = serializers.IntegerField()
    quantity = serializers.IntegerField()
    phone = serializers.CharField()
    order = serializers.CharField()


class NaverChatBotSerializer(serializers.Serializer):
    event = serializers.CharField()
