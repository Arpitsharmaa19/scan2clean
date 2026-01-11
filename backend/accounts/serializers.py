from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'phone', 'latitude', 'longitude', 'average_rating', 'total_ratings')
        read_only_fields = ('average_rating', 'total_ratings')
