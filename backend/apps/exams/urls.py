from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, QuestionResponseViewSet

router = DefaultRouter()
router.register(r'responses', QuestionResponseViewSet, basename='question-response')
router.register(r'',          ExamViewSet,             basename='exam')

urlpatterns = [path('', include(router.urls))]
