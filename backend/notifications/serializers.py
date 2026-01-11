from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = '__all__'

    def get_created_at(self, obj):
        return obj.created_at.strftime("%b %d, %H:%M")
