from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes as pc
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    AdminPasswordResetSerializer, CustomTokenObtainPairSerializer,
)
from .permissions import IsAdmin, IsAdminOrReadOwn


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('name')

    def get_permissions(self):
        if self.action == 'setup':
            return [AllowAny()]
        if self.action in ['list', 'create', 'destroy']:
            return [IsAdmin()]
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [IsAdminOrReadOwn()]
        if self.action == 'reset_password':
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update'] and not self.request.user.is_admin:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        qs    = super().get_queryset()
        role  = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        stype = self.request.query_params.get('student_type')
        if stype:
            qs = qs.filter(student_type=stype)
        return qs

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == 'GET':
            return Response(UserSerializer(request.user).data)
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user       = self.get_object()
        serializer = AdminPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password reset successfully.'})

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='needs-setup')
    def needs_setup(self, request):
        """
        Public endpoint — returns { needs_setup: true } when the database
        has no users at all.  The frontend checks this on startup to decide
        whether to show the first-run setup screen.
        """
        return Response({'needs_setup': not User.objects.exists()})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='setup')
    def setup(self, request):
        """
        Public endpoint — creates the very first teacher account.
        Refuses if ANY user already exists, so it cannot be exploited
        after initial setup.
        """
        if User.objects.exists():
            return Response(
                {'detail': 'Setup already completed. This endpoint is disabled.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserCreateSerializer(data={
            **request.data,
            'role':         'admin',
            'student_type': None,
        })
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_staff       = True
        user.is_superuser   = True
        user.save(update_fields=['is_staff', 'is_superuser'])

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )
