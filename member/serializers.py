from rest_framework import serializers


class IamportSmsCallbackSerializer(serializers.Serializer):
    imp_uid = serializers.CharField()
    merchant_uid = serializers.CharField()
