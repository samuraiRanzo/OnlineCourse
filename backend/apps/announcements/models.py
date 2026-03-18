import uuid
from django.db import models
from django.conf import settings


class Announcement(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course     = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='announcements'
    )
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    pinned     = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'announcements'
        ordering = ['-pinned', '-created_at']

    def __str__(self):
        return self.title


class AnnouncementRead(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    announcement = models.ForeignKey(
        Announcement, on_delete=models.CASCADE, related_name='reads'
    )
    student      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='announcement_reads', limit_choices_to={'role': 'student'}
    )
    read_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'announcement_reads'
        unique_together = ('announcement', 'student')

    def __str__(self):
        return f'{self.student.name} read "{self.announcement.title}"'
