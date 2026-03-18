from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes as pc
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdmin
from .models import Course, Lesson, Enrollment, LessonCompletion, LessonQuestion, LessonAnswer
from .serializers import (
    CourseSerializer, CourseListSerializer, LessonSerializer,
    EnrollmentSerializer, LessonCompletionSerializer,
    LessonQuestionSerializer, LessonAnswerSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related('lessons').all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'reorder_lessons']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        return CourseListSerializer if self.action == 'list' else CourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_student:
            enrolled_ids = self.request.user.enrollments.values_list('course_id', flat=True)
            qs = qs.filter(id__in=enrolled_ids)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin], url_path='reorder-lessons')
    def reorder_lessons(self, request, pk=None):
        """POST { "order": ["uuid1", "uuid2", ...] } — reorders lessons by index."""
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


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    # Must be multipart so DRF handles file uploads
    parser_classes   = [
        __import__('rest_framework.parsers', fromlist=['MultiPartParser']).MultiPartParser,
        __import__('rest_framework.parsers', fromlist=['JSONParser']).JSONParser,
    ]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Lesson.objects.filter(course_id=self.kwargs['course_pk']).order_by('order')

    def get_serializer_context(self):
        # Pass request so hls_url can build absolute URLs
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        course     = Course.objects.get(pk=self.kwargs['course_pk'])
        last_order = course.lessons.count()
        lesson     = serializer.save(course=course, order=last_order)
        # Kick off background transcoding if a video file was uploaded
        if lesson.type == 'video' and lesson.video_file:
            from .tasks import transcode_to_hls
            transcode_to_hls.delay(str(lesson.id))

    def perform_update(self, serializer):
        lesson = serializer.save()
        # Re-transcode if a new video file was uploaded on edit
        if lesson.type == 'video' and 'video_file' in self.request.FILES:
            lesson.hls_ready = False
            lesson.hls_path  = ''
            lesson.save(update_fields=['hls_ready', 'hls_path'])
            from .tasks import transcode_to_hls
            transcode_to_hls.delay(str(lesson.id))


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
        # Idempotent — visiting a lesson twice doesn't create duplicate records
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
    """
    Questions posted by students on a specific lesson.
    Nested under: /api/courses/<course_pk>/lessons/<lesson_pk>/questions/

    Rules:
    - Any enrolled student can POST a question
    - All enrolled students + teacher can GET questions
    - Only the author can edit their own question body
    - Teacher can toggle is_resolved on any question
    - Teacher and question author can delete
    """
    serializer_class = LessonQuestionSerializer
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
        # Students can only edit their own question body
        # Teacher can toggle is_resolved
        if request.user.is_student and question.author != request.user:
            return Response({'detail': 'You can only edit your own questions.'}, status=403)
        # Students cannot set is_resolved
        if request.user.is_student and 'is_resolved' in request.data:
            return Response({'detail': 'Only the teacher can resolve questions.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        if request.user.is_student and question.author != request.user:
            return Response({'detail': 'You can only delete your own questions.'}, status=403)
        return super().destroy(request, *args, **kwargs)


class LessonAnswerViewSet(viewsets.ModelViewSet):
    """
    Answers to a LessonQuestion.
    Nested under: /api/courses/<course_pk>/lessons/<lesson_pk>/questions/<question_pk>/answers/

    Rules:
    - Any enrolled student or teacher can POST an answer
    - Only the author can edit their own answer
    - Teacher and answer author can delete
    """
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
