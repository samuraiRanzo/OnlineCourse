import uuid
from django.db import models
from django.conf import settings


class Session(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course     = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='sessions'
    )
    label      = models.CharField(max_length=200)
    code       = models.CharField(max_length=6, unique=True, db_index=True)
    date       = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sessions'
        ordering = ['-date']

    def __str__(self):
        return f'{self.course.title} — {self.label} ({self.date})'


class Attendance(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session       = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendances')
    student       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='attendances', limit_choices_to={'role': 'student'}
    )
    checked_in_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'attendance'
        unique_together = ('session', 'student')

    def __str__(self):
        return f'{self.student.name} @ {self.session.label}'
