from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from apps.users.views import CustomTokenObtainPairView

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # JWT auth endpoints
    path('api/auth/login/',   CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(),          name='token_refresh'),
    path('api/auth/logout/',  TokenBlacklistView.as_view(),        name='token_blacklist'),

    # App routers
    path('api/users/',         include('apps.users.urls')),
    path('api/courses/',       include('apps.courses.urls')),
    path('api/attendance/',    include('apps.attendance.urls')),
    path('api/exams/',         include('apps.exams.urls')),
    path('api/certificates/',  include('apps.certificates.urls')),
    path('api/announcements/', include('apps.announcements.urls')),
]

# ── Media files ─────────────────────────────────────────────────────────
# In development Django serves media directly.
# In production Nginx serves /media/ — this line has no effect when DEBUG=False.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
