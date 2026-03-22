import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    A single in-app notification for one user.

    Types
    -----
    qa_answer       — someone replied to a lesson question the student posted
    exam_graded     — teacher graded an open answer in the student's exam result
    cert_issued     — a certificate was auto-issued for the student
    announcement    — a new announcement was posted in an enrolled course
    """

    class Type(models.TextChoices):
        QA_ANSWER    = 'qa_answer',    'Q&A Answer'
        EXAM_GRADED  = 'exam_graded',  'Exam Graded'
        CERT_ISSUED  = 'cert_issued',  'Certificate Issued'
        ANNOUNCEMENT = 'announcement', 'Announcement'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type       = models.CharField(max_length=20, choices=Type.choices)
    title      = models.CharField(max_length=200)
    body       = models.TextField(blank=True)
    # A frontend route the user lands on when clicking the notification,
    # e.g. "/my-courses/abc/lessons/xyz" or "/my-courses/abc/exam".
    link       = models.CharField(max_length=500, blank=True)
    is_read    = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.type}] → {self.recipient.name}: {self.title}'
