from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, LessonViewSet, EnrollmentViewSet, LessonCompletionViewSet,
    LessonQuestionViewSet, LessonAnswerViewSet, LessonAttachmentViewSet,
)

router = DefaultRouter()
router.register(r'enrollments', EnrollmentViewSet,       basename='enrollment')
router.register(r'completions', LessonCompletionViewSet, basename='completion')
router.register(r'',            CourseViewSet,           basename='course')

urlpatterns = [
    # ── Lessons ───────────────────────────────────────────────────────────────
    path('<uuid:course_pk>/lessons/', LessonViewSet.as_view({
        'get': 'list', 'post': 'create',
    }), name='course-lesson-list'),
    path('<uuid:course_pk>/lessons/<uuid:pk>/', LessonViewSet.as_view({
        'get':    'retrieve',
        'put':    'update',
        'patch':  'partial_update',
        'delete': 'destroy',
    }), name='course-lesson-detail'),

    # ── Lesson publish / unpublish ────────────────────────────────────────────
    path('<uuid:course_pk>/lessons/<uuid:pk>/publish/',   LessonViewSet.as_view({'post': 'publish'}),   name='lesson-publish'),
    path('<uuid:course_pk>/lessons/<uuid:pk>/unpublish/', LessonViewSet.as_view({'post': 'unpublish'}), name='lesson-unpublish'),

    # ── Student note on a lesson (GET = fetch/create blank, PATCH = upsert) ───
    path('<uuid:course_pk>/lessons/<uuid:pk>/note/', LessonViewSet.as_view({
        'get': 'note', 'patch': 'note',
    }), name='lesson-note'),

    # ── Attachments ───────────────────────────────────────────────────────────
    path('<uuid:course_pk>/lessons/<uuid:lesson_pk>/attachments/', LessonAttachmentViewSet.as_view({
        'get': 'list', 'post': 'create',
    }), name='lesson-attachment-list'),
    path('<uuid:course_pk>/lessons/<uuid:lesson_pk>/attachments/<uuid:pk>/', LessonAttachmentViewSet.as_view({
        'get': 'retrieve', 'delete': 'destroy',
    }), name='lesson-attachment-detail'),
    path('<uuid:course_pk>/lessons/<uuid:lesson_pk>/attachments/<uuid:pk>/stream/', LessonAttachmentViewSet.as_view({
        'get': 'stream',
    }), name='lesson-attachment-stream'),

    # ── Q&A ───────────────────────────────────────────────────────────────────
    path('<uuid:course_pk>/lessons/<uuid:lesson_pk>/questions/', LessonQuestionViewSet.as_view({
        'get': 'list', 'post': 'create',
    }), name='lesson-question-list'),
    path('<uuid:course_pk>/lessons/<uuid:lesson_pk>/questions/<uuid:pk>/', LessonQuestionViewSet.as_view({
        'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy',
    }), name='lesson-question-detail'),

    path('<uuid:course_pk>/lessons/<uuid:lesson_pk>/questions/<uuid:question_pk>/answers/', LessonAnswerViewSet.as_view({
        'get': 'list', 'post': 'create',
    }), name='lesson-answer-list'),
    path('<uuid:course_pk>/lessons/<uuid:lesson_pk>/questions/<uuid:question_pk>/answers/<uuid:pk>/', LessonAnswerViewSet.as_view({
        'patch': 'partial_update', 'delete': 'destroy',
    }), name='lesson-answer-detail'),

    path('', include(router.urls)),
]
