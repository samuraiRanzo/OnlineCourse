import uuid
from django.db import models
from django.conf import settings


class Certificate(models.Model):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='certificates', limit_choices_to={'role': 'student'}
    )
    course    = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='certificates'
    )
    cert_code = models.CharField(max_length=20, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'certificates'
        unique_together = ('student', 'course')
        ordering        = ['-issued_at']

    def __str__(self):
        return f'{self.cert_code} — {self.student.name} / {self.course.title}'
