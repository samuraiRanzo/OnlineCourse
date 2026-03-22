from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from apps.users.views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/login/',   CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(),          name='token_refresh'),
    path('api/auth/logout/',  TokenBlacklistView.as_view(),        name='token_blacklist'),

    path('api/users/',         include('apps.users.urls')),
    path('api/courses/',       include('apps.courses.urls')),
    path('api/attendance/',    include('apps.attendance.urls')),
    path('api/exams/',         include('apps.exams.urls')),
    path('api/certificates/',  include('apps.certificates.urls')),
    path('api/announcements/', include('apps.announcements.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/assignments/',   include('apps.assignments.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
