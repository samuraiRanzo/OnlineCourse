from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, QuestionViewSet, ExamResultViewSet

router = DefaultRouter()
router.register(r'results', ExamResultViewSet, basename='exam-result')
router.register(r'',        ExamViewSet,       basename='exam')

urlpatterns = [
    # Nested questions under an exam
    path('<uuid:exam_pk>/questions/', QuestionViewSet.as_view({
        'get': 'list', 'post': 'create',
    }), name='exam-question-list'),

    path('<uuid:exam_pk>/questions/<uuid:pk>/', QuestionViewSet.as_view({
        'get':    'retrieve',
        'put':    'update',
        'patch':  'partial_update',
        'delete': 'destroy',
    }), name='exam-question-detail'),

    # BUG 1 FIX: @action routes must be registered explicitly when the viewset
    # is NOT going through router.register().
    # POST  → upload / replace image
    # DELETE → remove image
    path('<uuid:exam_pk>/questions/<uuid:pk>/image/', QuestionViewSet.as_view({
        'post':   'image',
        'delete': 'image',
    }), name='exam-question-image'),

    path('', include(router.urls)),
]