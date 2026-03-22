"""
Notification signals.

Each receiver is lightweight: it imports lazily, constructs the minimum
data needed to build the notification, then calls Notification.objects.create().

Bulk operations (e.g. mark-all-read announcements) don't fire signals —
they go through the viewset action directly.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


# ── Q&A answer → notify the question author ───────────────────────────────────

@receiver(post_save, sender='courses.LessonAnswer')
def notify_qa_answer(sender, instance, created, **kwargs):
    """
    When a new answer is posted, notify the student who asked the question
    (unless the answerer IS the question author — no self-notification).
    """
    if not created:
        return

    answer   = instance
    question = answer.question
    student  = question.author

    # Don't notify if the answerer is the same person who asked
    if answer.author_id == student.id:
        return

    # Only notify students — teachers don't need in-app pings for their own Q&A
    if student.role != 'student':
        return

    from apps.notifications.models import Notification
    lesson = question.lesson
    course = lesson.course

    Notification.objects.create(
        recipient=student,
        type=Notification.Type.QA_ANSWER,
        title=f'New answer on "{lesson.title}"',
        body=f'{answer.author.name}: {answer.body[:120]}',
        link=f'/my-courses/{course.id}/lessons/{lesson.id}',
    )



# ── Exam grading notifications ─────────────────────────────────────────────────
# Exam result notifications (EXAM_GRADED type) are fired directly inside:
#   • apps.exams.views.ExamViewSet.submit          — fired after MCQ-only exams
#   • apps.exams.views.QuestionResponseViewSet.grade — fired once all open
#     questions have been graded by the teacher
#
# No signal is needed here because ExamResult no longer exists — the current
# model is ExamAttempt, and grading logic lives entirely in the view layer.


# ── Certificate issued → notify the student ───────────────────────────────────

@receiver(post_save, sender='certificates.Certificate')
def notify_cert_issued(sender, instance, created, **kwargs):
    if not created:
        return

    from apps.notifications.models import Notification
    cert    = instance
    student = cert.student
    course  = cert.course

    Notification.objects.create(
        recipient=student,
        type=Notification.Type.CERT_ISSUED,
        title=f'🎓 Certificate earned — {course.title}',
        body=f'Congratulations! Your certificate ({cert.cert_code}) has been issued.',
        link=f'/my-courses/{course.id}',
    )


# ── Announcement posted → notify all enrolled students ────────────────────────

@receiver(post_save, sender='announcements.Announcement')
def notify_announcement(sender, instance, created, **kwargs):
    """
    When a new announcement is created, send a notification to every student
    enrolled in that course.

    Bulk-creates notifications for efficiency — one INSERT instead of N.
    """
    if not created:
        return

    from apps.notifications.models import Notification
    from apps.courses.models import Enrollment

    ann     = instance
    course  = ann.course

    # Collect all enrolled student IDs
    enrolled = Enrollment.objects.filter(
        course=course
    ).select_related('student').values_list('student', flat=True)

    if not enrolled:
        return

    # Get User objects for all enrolled students
    from django.contrib.auth import get_user_model
    User = get_user_model()
    students = User.objects.filter(id__in=enrolled, role='student')

    notifications = [
        Notification(
            recipient=student,
            type=Notification.Type.ANNOUNCEMENT,
            title=f'📣 {ann.title}',
            body=ann.body[:160],
            link=f'/notices',
        )
        for student in students
    ]
    Notification.objects.bulk_create(notifications, ignore_conflicts=True)
