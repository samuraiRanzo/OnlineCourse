from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SessionViewSet, CheckInView

router = DefaultRouter()
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'checkin',  CheckInView,    basename='checkin')

urlpatterns = [path('', include(router.urls))]
