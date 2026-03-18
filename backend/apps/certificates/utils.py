import random
import string


def _generate_cert_code():
    from .models import Certificate
    while True:
        code = 'CERT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Certificate.objects.filter(cert_code=code).exists():
            return code


def check_completion(student, course) -> bool:
    """
    Returns True if the student has met all completion requirements.

    Online  : all lessons visited AND latest exam score >= 60
    Onsite  : attendance >= course threshold AND latest exam score >= 60
    """
    from apps.exams.models import ExamResult
    from apps.courses.models import Enrollment, LessonCompletion

    # Must have passed the exam
    best_result = ExamResult.objects.filter(
        exam__course=course, student=student
    ).order_by('-score').first()
    if not best_result or best_result.score < 60:
        return False

    if student.student_type == 'online':
        enrollment = Enrollment.objects.filter(student=student, course=course).first()
        if not enrollment:
            return False
        total = course.lessons.count()
        done  = LessonCompletion.objects.filter(enrollment=enrollment).count()
        return total > 0 and done >= total

    if student.student_type == 'onsite':
        from apps.attendance.utils import get_attendance_stats
        stats     = get_attendance_stats(str(student.id), str(course.id))
        threshold = course.attendance_threshold
        return stats['pct'] >= threshold

    return False


def maybe_issue_certificate(student, course):
    """
    Issues a certificate if the student has completed the course and
    one hasn't been issued yet. Returns (certificate, created) tuple.
    """
    from .models import Certificate
    existing = Certificate.objects.filter(student=student, course=course).first()
    if existing:
        return existing, False
    if not check_completion(student, course):
        return None, False
    cert = Certificate.objects.create(
        student=student,
        course=course,
        cert_code=_generate_cert_code(),
    )
    return cert, True
