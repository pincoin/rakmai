from rest_framework import serializers


class IamportSmsCallbackSerializer(serializers.Serializer):
    imp_uid = serializers.CharField()
