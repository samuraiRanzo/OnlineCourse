from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from apps.users.permissions import IsAdmin
from .models import Course, Lesson, Enrollment, LessonCompletion, LessonQuestion, LessonAnswer, LessonAttachment
from .serializers import (
    CourseSerializer, CourseListSerializer, LessonSerializer,
    EnrollmentSerializer, LessonCompletionSerializer,
    LessonQuestionSerializer, LessonAnswerSerializer,
    LessonAttachmentSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related('lessons').all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'reorder_lessons', 'publish', 'unpublish']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        return CourseListSerializer if self.action == 'list' else CourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_student:
            # Students only see published courses they are enrolled in
            enrolled_ids = self.request.user.enrollments.values_list('course_id', flat=True)
            qs = qs.filter(id__in=enrolled_ids, status='published')
        return qs

    # ── Publish / Unpublish ───────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """
        Publishes a course. Sets published_at if this is the first time.
        Returns the updated course object.
        """
        course = self.get_object()
        if course.status == 'published':
            return Response({'detail': 'Course is already published.'}, status=400)
        course.status = 'published'
        if not course.published_at:
            course.published_at = timezone.now()
        course.save(update_fields=['status', 'published_at'])
        return Response(CourseSerializer(course, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='unpublish')
    def unpublish(self, request, pk=None):
        """Reverts a course to draft. Students immediately lose access."""
        course = self.get_object()
        if course.status == 'draft':
            return Response({'detail': 'Course is already a draft.'}, status=400)
        course.status = 'draft'
        course.save(update_fields=['status'])
        return Response(CourseSerializer(course, context={'request': request}).data)

    # ── Reorder lessons ───────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin], url_path='reorder-lessons')
    def reorder_lessons(self, request, pk=None):
        course  = self.get_object()
        ordered = request.data.get('order', [])
        if not isinstance(ordered, list):
            return Response({'detail': 'order must be a list of lesson IDs.'}, status=400)
        lessons = {str(l.id): l for l in course.lessons.all()}
        for idx, lid in enumerate(ordered):
            if lid in lessons:
                lessons[lid].order = idx
        Lesson.objects.bulk_update(lessons.values(), ['order'])
        return Response(LessonSerializer(course.lessons.order_by('order'), many=True).data)

    @action(detail=True, methods=['get'], url_path='all-questions')
    def all_questions(self, request, pk=None):
        """Returns all questions for all lessons in this course."""
        from .models import LessonQuestion
        questions = LessonQuestion.objects.filter(lesson__course_id=pk).select_related('author', 'lesson')
        serializer = LessonQuestionSerializer(questions, many=True)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    parser_classes   = [
        __import__('rest_framework.parsers', fromlist=['MultiPartParser']).MultiPartParser,
        __import__('rest_framework.parsers', fromlist=['JSONParser']).JSONParser,
    ]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'publish', 'unpublish']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Lesson.objects.filter(course_id=self.kwargs['course_pk']).order_by('order')
        # Students only see published lessons
        if self.request.user.is_student:
            qs = qs.filter(status='published')
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        course     = Course.objects.get(pk=self.kwargs['course_pk'])
        last_order = course.lessons.count()
        lesson     = serializer.save(course=course, order=last_order)
        if lesson.type == 'video' and lesson.video_file:
            from .tasks import transcode_to_hls
            transcode_to_hls.delay(str(lesson.id))

    def perform_update(self, serializer):
        lesson = serializer.save()
        if lesson.type == 'video' and 'video_file' in self.request.FILES:
            lesson.hls_ready = False
            lesson.hls_path  = ''
            lesson.save(update_fields=['hls_ready', 'hls_path'])
            from .tasks import transcode_to_hls
            transcode_to_hls.delay(str(lesson.id))

    # ── Lesson-level publish / unpublish ──────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, course_pk=None, pk=None):
        lesson = self.get_object()
        if lesson.status == 'published':
            return Response({'detail': 'Lesson is already published.'}, status=400)
        lesson.status = 'published'
        lesson.save(update_fields=['status'])
        return Response(LessonSerializer(lesson, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='unpublish')
    def unpublish(self, request, course_pk=None, pk=None):
        lesson = self.get_object()
        if lesson.status == 'draft':
            return Response({'detail': 'Lesson is already a draft.'}, status=400)
        lesson.status = 'draft'
        lesson.save(update_fields=['status'])
        return Response(LessonSerializer(lesson, context={'request': request}).data)


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Enrollment.objects.select_related('student', 'course').prefetch_related('completions')
        if self.request.user.is_student:
            return qs.filter(student=self.request.user)
        student_id = self.request.query_params.get('student')
        course_id  = self.request.query_params.get('course')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class LessonCompletionViewSet(viewsets.ModelViewSet):
    serializer_class   = LessonCompletionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = LessonCompletion.objects.select_related('enrollment', 'lesson')
        if self.request.user.is_student:
            return qs.filter(enrollment__student=self.request.user)
        return qs

    def create(self, request, *args, **kwargs):
        obj, created = LessonCompletion.objects.get_or_create(
            enrollment_id=request.data.get('enrollment'),
            lesson_id=request.data.get('lesson'),
        )
        return Response(
            self.get_serializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ── Q&A ──────────────────────────────────────────────────────────────────

class LessonQuestionViewSet(viewsets.ModelViewSet):
    serializer_class  = LessonQuestionSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return LessonQuestion.objects.filter(
            lesson_id=self.kwargs['lesson_pk']
        ).select_related('author').prefetch_related('answers__author')

    def get_permissions(self):
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        lesson = Lesson.objects.get(pk=self.kwargs['lesson_pk'])
        serializer.save(author=self.request.user, lesson=lesson)

    def partial_update(self, request, *args, **kwargs):
        question = self.get_object()
        if request.user.is_student and question.author != request.user:
            return Response({'detail': 'You can only edit your own questions.'}, status=403)
        if request.user.is_student and 'is_resolved' in request.data:
            return Response({'detail': 'Only the teacher can resolve questions.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        if request.user.is_student and question.author != request.user:
            return Response({'detail': 'You can only delete your own questions.'}, status=403)
        return super().destroy(request, *args, **kwargs)


class LessonAnswerViewSet(viewsets.ModelViewSet):
    serializer_class  = LessonAnswerSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return LessonAnswer.objects.filter(
            question_id=self.kwargs['question_pk']
        ).select_related('author')

    def get_permissions(self):
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        question = LessonQuestion.objects.get(pk=self.kwargs['question_pk'])
        serializer.save(author=self.request.user, question=question)

    def partial_update(self, request, *args, **kwargs):
        answer = self.get_object()
        if answer.author != request.user:
            return Response({'detail': 'You can only edit your own answers.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        answer = self.get_object()
        if request.user.is_student and answer.author != request.user:
            return Response({'detail': 'You can only delete your own answers.'}, status=403)
        return super().destroy(request, *args, **kwargs)

class LessonAttachmentViewSet(viewsets.ModelViewSet):
    """
    File attachments on a lesson.
    Nested under: /api/courses/<course_pk>/lessons/<lesson_pk>/attachments/

    - Teacher: upload (POST multipart), delete
    - Students: list + download URL (read-only)
    - Files are stored under MEDIA_ROOT/lessons/<lesson_id>/attachments/
    """
    serializer_class  = LessonAttachmentSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    parser_classes    = [
        __import__('rest_framework.parsers', fromlist=['MultiPartParser']).MultiPartParser,
        __import__('rest_framework.parsers', fromlist=['JSONParser']).JSONParser,
    ]

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return LessonAttachment.objects.filter(
            lesson_id=self.kwargs['lesson_pk']
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        lesson = Lesson.objects.get(pk=self.kwargs['lesson_pk'])
        uploaded = self.request.FILES.get('file')

        # Use the provided name, or fall back to the original filename
        name      = self.request.data.get('name', '').strip() or uploaded.name
        file_size = uploaded.size if uploaded else 0

        serializer.save(
            lesson=lesson,
            name=name,
            file_size=file_size,
        )