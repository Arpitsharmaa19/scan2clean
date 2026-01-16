from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login
from .serializers import UserSerializer
from .models import User

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    identifier = request.data.get('username')
    password = request.data.get('password')
    
    # Try username first
    user = authenticate(username=identifier, password=password)
    
    # Try email if username fails
    if not user:
        try:
            user_obj = User.objects.filter(email__iexact=identifier).first()
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)
        except Exception:
            pass

    if user:
        login(request, user)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    role = request.data.get('role', 'citizen')
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password, email=email, role=role)
    login(request, user)
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
