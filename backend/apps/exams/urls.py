from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, QuestionViewSet, ExamResultViewSet

router = DefaultRouter()
router.register(r'results',  ExamResultViewSet, basename='exam-result')
router.register(r'',         ExamViewSet,       basename='exam')

urlpatterns = [
    # Nested questions: /api/exams/{exam_pk}/questions/
    path('<uuid:exam_pk>/questions/', QuestionViewSet.as_view({
        'get': 'list', 'post': 'create',
    }), name='exam-question-list'),
    path('<uuid:exam_pk>/questions/<uuid:pk>/', QuestionViewSet.as_view({
        'get': 'retrieve', 'put': 'update',
        'patch': 'partial_update', 'delete': 'destroy',
    }), name='exam-question-detail'),
    path('', include(router.urls)),
]
