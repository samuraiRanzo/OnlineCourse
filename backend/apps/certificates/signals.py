from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='attendance.Attendance')
def check_cert_on_attendance(sender, instance, created, **kwargs):
    """
    After an onsite student checks in, re-evaluate whether they now
    meet the attendance threshold and issue a certificate if so.
    """
    if not created:
        return
    from .utils import maybe_issue_certificate
    student = instance.student
    course  = instance.session.course
    if student.student_type == 'onsite':
        maybe_issue_certificate(student, course)
