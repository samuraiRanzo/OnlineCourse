import uuid
from django.db import models
from django.conf import settings


class Assignment(models.Model):
    """
    A piece of work a teacher assigns to students on a specific lesson.
    Students can submit a text answer, a file, or both.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson      = models.ForeignKey(
        'courses.Lesson', on_delete=models.CASCADE, related_name='assignments'
    )
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date    = models.DateTimeField(null=True, blank=True)
    max_score   = models.PositiveIntegerField(default=100)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assignments'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.lesson.title} — {self.title}'


def submission_upload_path(instance, filename):
    """submissions/<assignment_id>/<student_id>/<filename>"""
    return f'submissions/{instance.assignment_id}/{instance.student_id}/{filename}'


class Submission(models.Model):
    """
    One submission per student per assignment (unique_together).
    Students can resubmit until the teacher grades it.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment  = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name='submissions'
    )
    student     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='submissions', limit_choices_to={'role': 'student'}
    )
    file        = models.FileField(
        upload_to=submission_upload_path, null=True, blank=True,
        help_text='Optional file upload — PDF, DOCX, image, etc.'
    )
    text_answer = models.TextField(blank=True)

    # Grading — populated by teacher
    score      = models.PositiveIntegerField(null=True, blank=True)
    feedback   = models.TextField(blank=True)
    graded_at  = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'submissions'
        unique_together = ('student', 'assignment')
        ordering        = ['-updated_at']

    def __str__(self):
        return f'{self.student.name} → {self.assignment.title}'

    @property
    def is_graded(self):
        return self.score is not None
