"""
HOW TO INTEGRATE final_grade INTO YOUR CourseViewSet
=====================================================

In apps/courses/views.py, add these imports at the top (if not already present):

    from django.db.models import Avg, Max, F, FloatField, ExpressionWrapper

Then paste the two methods below directly inside your CourseViewSet class,
alongside your existing `analytics`, `all_questions`, etc. actions.

The file final_grade_action.py (already in your outputs) contains the full
standalone logic — copy the @action and _all_students_final_grades function
verbatim into CourseViewSet.

Endpoint produced:
  GET /api/courses/{id}/final-grade/               → current student's grade
  GET /api/courses/{id}/final-grade/?student_id=X  → teacher: one student
  GET /api/courses/{id}/final-grade/               → teacher (no param): all students
"""

from django.db.models import Avg, Max, F, FloatField, ExpressionWrapper, Sum
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


# ── Paste this @action into CourseViewSet ─────────────────────────────────────

@action(detail=True, methods=['get'], url_path='final-grade',
        permission_classes=[IsAuthenticated])
def final_grade(self, request, pk=None):
    """
    GET /api/courses/{id}/final-grade/
    GET /api/courses/{id}/final-grade/?student_id=<uuid>   (teacher only)

    Returns weighted final grade:
      final = exam_best_score * (exam_weight/100)
            + assignment_avg  * (assignment_weight/100)
    """
    course = self.get_object()

    if request.user.is_student:
        student = request.user
    else:
        student_id = request.query_params.get('student_id')
        if not student_id:
            return _all_students_final_grades(course)
        from apps.users.models import User
        try:
            student = User.objects.get(pk=student_id)
        except User.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=404)

    from apps.exams.models import ExamAttempt
    from apps.assignments.models import Submission, Assignment

    exam              = getattr(course, 'exam', None)
    exam_weight       = exam.exam_weight       if exam else 70
    assignment_weight = exam.assignment_weight if exam else 30
    passing_score     = exam.passing_score     if exam else 60

    # ── Exam ──────────────────────────────────────────────────────────────────
    best_attempt    = None
    exam_score      = None
    submitted_count = 0
    retakes_remaining = None

    if exam:
        submitted_count = ExamAttempt.objects.filter(
            student=student, exam=exam, is_submitted=True
        ).count()
        best_attempt = (
            ExamAttempt.objects
            .filter(student=student, exam=exam, is_submitted=True)
            .order_by('-score')
            .first()
        )
        if best_attempt:
            exam_score = best_attempt.score
        if exam.max_retakes > 0:
            retakes_remaining = max(0, exam.max_retakes - submitted_count)

    # ── Assignments ───────────────────────────────────────────────────────────
    total_assignments = Assignment.objects.filter(lesson__course=course).count()
    graded_submissions = Submission.objects.filter(
        student=student,
        assignment__lesson__course=course,
        score__isnull=False,
    ).annotate(
        pct=ExpressionWrapper(
            F('score') * 100.0 / F('assignment__max_score'),
            output_field=FloatField(),
        )
    )
    graded_count   = graded_submissions.count()
    assignment_avg = graded_submissions.aggregate(avg=Avg('pct'))['avg']
    if assignment_avg is not None:
        assignment_avg = round(assignment_avg, 1)

    # ── Weighted final ─────────────────────────────────────────────────────────
    if exam_score is not None and assignment_avg is not None:
        final_grade_value = round(
            exam_score * (exam_weight / 100)
            + assignment_avg * (assignment_weight / 100),
            1
        )
    elif exam_score is not None:
        final_grade_value = round(exam_score, 1)
    elif assignment_avg is not None:
        final_grade_value = round(assignment_avg, 1)
    else:
        final_grade_value = None

    passed = (final_grade_value >= passing_score) if final_grade_value is not None else None

    return Response({
        'student_id':          str(student.pk),
        'student_name':        student.name,
        'course_id':           str(course.pk),
        'exam_weight':         exam_weight,
        'assignment_weight':   assignment_weight,
        'passing_score':       passing_score,
        'exam_score':          exam_score,
        'exam_attempt_id':     str(best_attempt.pk) if best_attempt else None,
        'submitted_count':     submitted_count,
        'retakes_remaining':   retakes_remaining,
        'assignment_avg':      assignment_avg,
        'graded_submissions':  graded_count,
        'total_assignments':   total_assignments,
        'final_grade':         final_grade_value,
        'passed':              passed,
    })


# ── Paste this helper function OUTSIDE CourseViewSet (module-level) ────────────

def _all_students_final_grades(course):
    """Teacher shortcut: final grades for all enrolled students."""
    from apps.exams.models import ExamAttempt
    from apps.assignments.models import Submission, Assignment

    exam              = getattr(course, 'exam', None)
    exam_weight       = exam.exam_weight       if exam else 70
    assignment_weight = exam.assignment_weight if exam else 30
    passing_score     = exam.passing_score     if exam else 60
    total_assignments = Assignment.objects.filter(lesson__course=course).count()

    results = []
    for enroll in course.enrollments.select_related('student').all():
        student = enroll.student

        best = (
            ExamAttempt.objects
            .filter(student=student, exam=exam, is_submitted=True)
            .aggregate(best=Max('score'))['best']
            if exam else None
        )

        graded = Submission.objects.filter(
            student=student,
            assignment__lesson__course=course,
            score__isnull=False,
        ).annotate(
            pct=ExpressionWrapper(
                F('score') * 100.0 / F('assignment__max_score'),
                output_field=FloatField(),
            )
        )
        avg_asgn = graded.aggregate(avg=Avg('pct'))['avg']
        if avg_asgn:
            avg_asgn = round(avg_asgn, 1)

        if best is not None and avg_asgn is not None:
            final = round(
                best * (exam_weight / 100) + avg_asgn * (assignment_weight / 100), 1
            )
        elif best is not None:
            final = round(best, 1)
        elif avg_asgn is not None:
            final = round(avg_asgn, 1)
        else:
            final = None

        results.append({
            'student_id':           str(student.pk),
            'student_name':         student.name,
            'student_email':        student.email,
            'student_type':         student.student_type,
            'exam_score':           best,
            'assignment_avg':       avg_asgn,
            'graded_submissions':   graded.count(),
            'total_assignments':    total_assignments,
            'final_grade':          final,
            'passed':               (final >= passing_score) if final is not None else None,
        })

    return Response({
        'exam_weight':       exam_weight,
        'assignment_weight': assignment_weight,
        'passing_score':     passing_score,
        'students':          results,
    })
