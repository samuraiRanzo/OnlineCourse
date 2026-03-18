import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class Course(models.Model):

    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        PUBLISHED = 'published', 'Published'

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title                = models.CharField(max_length=200)
    description          = models.TextField(blank=True)
    icon                 = models.CharField(max_length=10, default='📚')
    attendance_threshold = models.PositiveIntegerField(default=75)
    status               = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT,
        help_text='Only published courses are visible to students'
    )
    published_at         = models.DateTimeField(
        null=True, blank=True,
        help_text='Set automatically when status changes to published'
    )
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED


class Lesson(models.Model):

    class Type(models.TextChoices):
        TEXT  = 'text',  'Text'
        VIDEO = 'video', 'Video'

    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        PUBLISHED = 'published', 'Published'

    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course    = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title     = models.CharField(max_length=200)
    type      = models.CharField(max_length=10, choices=Type.choices, default=Type.TEXT)
    content   = models.TextField(blank=True)
    video_url = models.URLField(blank=True,
                    help_text='YouTube embed URL — used when video_file is not set')
    # ── Self-hosted video fields ──────────────────────────────────────
    video_file = models.FileField(
        upload_to='videos/raw/', null=True, blank=True,
        help_text='Original uploaded video file — transcoded to HLS by Celery'
    )
    hls_path  = models.CharField(
        max_length=500, blank=True,
        help_text='Relative path to index.m3u8 under MEDIA_ROOT'
    )
    hls_ready = models.BooleanField(
        default=False,
        help_text='True once FFmpeg transcoding is complete'
    )
    status    = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT,
        help_text='Only published lessons are visible to students'
    )
    order     = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'lessons'
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.title}'

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED


class Enrollment(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='enrollments', limit_choices_to={'role': 'student'}
    )
    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'enrollments'
        unique_together = ('student', 'course')
        ordering      = ['-enrolled_at']

    def __str__(self):
        return f'{self.student.name} → {self.course.title}'


class LessonCompletion(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment   = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='completions')
    lesson       = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table      = 'lesson_completions'
        unique_together = ('enrollment', 'lesson')

    def __str__(self):
        return f'{self.enrollment} ✓ {self.lesson.title}'


class LessonQuestion(models.Model):
    """A question posted by a student on a specific lesson."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson     = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    author     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_questions'
    )
    body       = models.TextField()
    is_resolved = models.BooleanField(
        default=False,
        help_text='Teacher marks this True once the question is answered satisfactorily'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lesson_questions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.name}: {self.body[:60]}'


class LessonAnswer(models.Model):
    """A reply to a LessonQuestion — can come from student or teacher."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question   = models.ForeignKey(LessonQuestion, on_delete=models.CASCADE, related_name='answers')
    author     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_answers'
    )
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lesson_answers'
        ordering = ['created_at']

    def __str__(self):
        return f'Reply by {self.author.name}'