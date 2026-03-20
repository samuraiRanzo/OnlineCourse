import uuid
from django.db import models
from django.conf import settings


class Exam(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course      = models.OneToOneField(
        'courses.Course', on_delete=models.CASCADE, related_name='exam'
    )
    title       = models.CharField(max_length=200)
    max_retakes = models.PositiveIntegerField(
        default=0,
        help_text='Max number of retakes allowed. 0 = unlimited.'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exams'

    def __str__(self):
        return f'Exam: {self.title}'


class Question(models.Model):
    class Type(models.TextChoices):
        MCQ  = 'mcq',  'Multiple Choice'
        OPEN = 'open', 'Open Answer'

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam          = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    type          = models.CharField(max_length=10, choices=Type.choices, default=Type.MCQ)
    text          = models.TextField()
    image         = models.ImageField(
        upload_to='exam_questions/', null=True, blank=True,
        help_text='Optional image displayed above the question text'
    )
    # options and correct_index only used for MCQ questions
    options       = models.JSONField(default=list, blank=True)
    correct_index = models.PositiveIntegerField(null=True, blank=True)
    order         = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'questions'
        ordering = ['order']

    def __str__(self):
        return f'Q{self.order}: {self.text[:60]}'


class ExamResult(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam         = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='exam_results', limit_choices_to={'role': 'student'}
    )
    score        = models.PositiveIntegerField(help_text='MCQ percentage score 0-100')
    answers      = models.JSONField(default=dict, help_text='{ question_index: answer }')
    open_grades  = models.JSONField(default=dict, help_text='{ question_index: grade_label }')
    submitted_at = models.DateTimeField(auto_now_add=True)
    attempt      = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'exam_results'
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.student.name} — {self.exam.title} ({self.score}%)'