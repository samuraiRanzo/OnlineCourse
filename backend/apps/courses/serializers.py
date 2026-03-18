from rest_framework import serializers
from django.conf import settings
from .models import Course, Lesson, Enrollment, LessonCompletion, LessonQuestion, LessonAnswer


class LessonSerializer(serializers.ModelSerializer):
    # Absolute URL to the .m3u8 playlist — consumed directly by hls.js
    hls_url = serializers.SerializerMethodField()

    class Meta:
        model  = Lesson
        fields = [
            'id', 'title', 'type', 'content', 'video_url', 'order',
            # self-hosted video
            'video_file', 'hls_path', 'hls_ready', 'hls_url',
        ]
        extra_kwargs = {
            'video_file': {'write_only': True},  # don't expose raw file path to students
            'hls_path':   {'read_only': True},
            'hls_ready':  {'read_only': True},
        }

    def get_hls_url(self, obj):
        """
        Returns the full URL to the .m3u8 playlist.
        - Supabase Storage: MEDIA_URL already contains the full CDN base URL
          e.g. https://xxx.supabase.co/storage/v1/object/public/learnforge-media/
          so we just concatenate hls_path.
        - Local dev: build absolute URL from request.
        """
        if not obj.hls_ready or not obj.hls_path:
            return None

        media_url = settings.MEDIA_URL

        # Supabase Storage — MEDIA_URL is already a full https:// URL
        if media_url.startswith('http'):
            return f'{media_url.rstrip("/")}/{obj.hls_path}'

        # Local dev — build absolute URL from the request
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'{media_url}{obj.hls_path}')
        return f'{media_url}{obj.hls_path}'


class CourseSerializer(serializers.ModelSerializer):
    lessons      = LessonSerializer(many=True, read_only=True)
    lesson_count = serializers.IntegerField(source='lessons.count', read_only=True)

    class Meta:
        model  = Course
        fields = ['id', 'title', 'description', 'icon',
                  'attendance_threshold', 'created_at', 'lessons', 'lesson_count', 'exam']
        read_only_fields = ['id', 'created_at']


class CourseListSerializer(serializers.ModelSerializer):
    lesson_count = serializers.IntegerField(source='lessons.count', read_only=True)

    class Meta:
        model  = Course
        fields = ['id', 'title', 'description', 'icon',
                  'attendance_threshold', 'created_at', 'lesson_count']
        read_only_fields = ['id', 'created_at']


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
        total = obj.course.lessons.count()
        if total == 0:
            return 0
        return round((obj.completions.count() / total) * 100)


class LessonCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LessonCompletion
        fields = ['id', 'enrollment', 'lesson', 'completed_at']
        read_only_fields = ['id', 'completed_at']


# ── Q&A ──────────────────────────────────────────────────────────────────

class LessonAnswerSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    is_teacher  = serializers.SerializerMethodField()

    class Meta:
        model  = LessonAnswer
        fields = ['id', 'question', 'author', 'author_name', 'is_teacher',
                  'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at','question']

    def get_is_teacher(self, obj):
        return obj.author.role == 'admin'


class LessonQuestionSerializer(serializers.ModelSerializer):
    author_name  = serializers.CharField(source='author.name', read_only=True)
    answers      = LessonAnswerSerializer(many=True, read_only=True)
    answer_count = serializers.IntegerField(source='answers.count', read_only=True)

    class Meta:
        model  = LessonQuestion
        fields = ['id', 'lesson', 'author', 'author_name',
                  'body', 'is_resolved', 'created_at', 'updated_at',
                  'answers', 'answer_count']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at','lesson']
