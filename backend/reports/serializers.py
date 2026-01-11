from rest_framework import serializers
from .models import WasteReport, SupportTicket

class WasteReportSerializer(serializers.ModelSerializer):
    citizen_name = serializers.ReadOnlyField(source='citizen.username')
    worker_name = serializers.ReadOnlyField(source='assigned_worker.username')

    class Meta:
        model = WasteReport
        fields = '__all__'

class SupportTicketSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = SupportTicket
        fields = '__all__'
