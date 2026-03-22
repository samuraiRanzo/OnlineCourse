from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from .models import (
    Course, Lesson, Enrollment, LessonCompletion,
    LessonQuestion, LessonAnswer, LessonAttachment, LessonNote,
)


class LessonAttachmentSerializer(serializers.ModelSerializer):
    stream_url = serializers.SerializerMethodField()
    extension  = serializers.CharField(read_only=True)

    class Meta:
        model  = LessonAttachment
        fields = ['id', 'name', 'file', 'file_size', 'extension', 'stream_url', 'uploaded_at']
        read_only_fields = ['id', 'file_size', 'extension', 'stream_url', 'uploaded_at']
        extra_kwargs = {
            'file': {'write_only': True}
        }

    def get_stream_url(self, obj):
        if not obj.file or not obj.file.name:
            return None
        request = self.context.get('request')
        from django.urls import reverse
        try:
            view      = self.context.get('view')
            course_pk = view.kwargs.get('course_pk') if view else None
            lesson_pk = view.kwargs.get('lesson_pk') if view else None
            if course_pk and lesson_pk:
                path = f'/api/courses/{course_pk}/lessons/{lesson_pk}/attachments/{obj.id}/stream/'
                if request:
                    return request.build_absolute_uri(path)
                return path
        except Exception:
            pass
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class LessonSerializer(serializers.ModelSerializer):
    hls_url     = serializers.SerializerMethodField()
    attachments = LessonAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model  = Lesson
        fields = [
            'id', 'title', 'type', 'content', 'video_url', 'order',
            'status',
            'video_file', 'hls_path', 'hls_ready', 'hls_url',
            'attachments',
        ]
        extra_kwargs = {
            'video_file': {'write_only': True},
            'hls_path':   {'read_only': True},
            'hls_ready':  {'read_only': True},
        }

    def get_hls_url(self, obj):
        if not obj.hls_ready or not obj.hls_path:
            return None
        media_url = settings.MEDIA_URL
        if media_url.startswith('http'):
            return f'{media_url.rstrip("/")}/{obj.hls_path}'
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'{media_url}{obj.hls_path}')
        return f'{media_url}{obj.hls_path}'


class CourseSerializer(serializers.ModelSerializer):
    lessons      = serializers.SerializerMethodField()
    lesson_count = serializers.SerializerMethodField()

    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'description', 'icon',
            'attendance_threshold', 'status', 'published_at',
            'created_at', 'lessons', 'lesson_count', 'exam'
        ]
        read_only_fields = ['id', 'created_at', 'published_at']

    def get_lessons(self, obj):
        request = self.context.get('request')
        qs = obj.lessons.all()
        if request and request.user.is_authenticated and request.user.is_student:
            qs = qs.filter(status='published')
        return LessonSerializer(qs, many=True, context=self.context).data

    def get_lesson_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.is_student:
            return obj.lessons.filter(status='published').count()
        return obj.lessons.count()


class CourseListSerializer(serializers.ModelSerializer):
    lesson_count           = serializers.SerializerMethodField()
    published_lesson_count = serializers.SerializerMethodField()

    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'description', 'icon',
            'attendance_threshold', 'status', 'published_at',
            'created_at', 'lesson_count', 'published_lesson_count', 'exam'
        ]
        read_only_fields = ['id', 'created_at', 'published_at']

    def get_lesson_count(self, obj):
        return obj.lessons.count()

    def get_published_lesson_count(self, obj):
        return obj.lessons.filter(status='published').count()


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name          = serializers.CharField(source='student.name',         read_only=True)
    student_email         = serializers.CharField(source='student.email',        read_only=True)
    student_type          = serializers.CharField(source='student.student_type', read_only=True)
    course_title          = serializers.CharField(source='course.title',         read_only=True)
    completed_lesson_ids  = serializers.SerializerMethodField()
    lesson_completion_pct = serializers.SerializerMethodField()

    class Meta:
        model  = Enrollment
        fields = [
            'id', 'student', 'student_name', 'student_email', 'student_type',
            'course', 'course_title', 'enrolled_at',
            'completed_lesson_ids', 'lesson_completion_pct',
        ]
        read_only_fields = ['id', 'enrolled_at']

    def get_completed_lesson_ids(self, obj):
        return list(obj.completions.values_list('lesson_id', flat=True))

    def get_lesson_completion_pct(self, obj):
        total = obj.course.lessons.filter(status='published').count()
        if total == 0:
            return 0
        return round((obj.completions.count() / total) * 100)


class LessonCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LessonCompletion
        fields = ['id', 'enrollment', 'lesson', 'completed_at']
        read_only_fields = ['id', 'completed_at']


# ── Q&A ──────────────────────────────────────────────────────────────────────

class LessonAnswerSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    is_teacher  = serializers.SerializerMethodField()

    class Meta:
        model  = LessonAnswer
        fields = ['id', 'question', 'author', 'author_name', 'is_teacher',
                  'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'question']

    def get_is_teacher(self, obj):
        return obj.author.role == 'admin'


class LessonQuestionSerializer(serializers.ModelSerializer):
    author_name  = serializers.CharField(source='author.name',   read_only=True)
    # Lesson title — useful for the teacher Q&A inbox view where questions
    # from all lessons in a course are displayed together.
    lesson_title = serializers.CharField(source='lesson.title',  read_only=True)
    answers      = LessonAnswerSerializer(many=True, read_only=True)
    answer_count = serializers.IntegerField(source='answers.count', read_only=True)

    class Meta:
        model  = LessonQuestion
        fields = [
            'id', 'lesson', 'lesson_title', 'author', 'author_name',
            'body', 'is_resolved', 'created_at', 'updated_at',
            'answers', 'answer_count',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'lesson']


# ── Notes ─────────────────────────────────────────────────────────────────────

class LessonNoteSerializer(serializers.ModelSerializer):
    """
    Private per-student note on a lesson.
    student and lesson are set by the view — never supplied by the client.
    """
    class Meta:
        model  = LessonNote
        fields = ['id', 'student', 'lesson', 'body', 'updated_at']
        read_only_fields = ['id', 'student', 'lesson', 'updated_at']
