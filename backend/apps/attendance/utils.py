def get_attendance_stats(student_id, course_id):
    """
    Returns dict: { attended, total, pct }
    Imported by certificates/signals.py and exams/views.py
    so the calculation lives in one place.
    """
    from .models import Session, Attendance
    sessions = Session.objects.filter(course_id=course_id)
    total    = sessions.count()
    if total == 0:
        return {'attended': 0, 'total': 0, 'pct': 0}
    attended = Attendance.objects.filter(
        session__in=sessions, student_id=student_id
    ).count()
    pct = round((attended / total) * 100)
    return {'attended': attended, 'total': total, 'pct': pct}
