"""
ADD this action to CourseViewSet inside apps/courses/views.py.

It computes the weighted final grade for a student:
  final = exam_best_score * (exam_weight/100)
        + assignment_avg  * (assignment_weight/100)

Query params:
  ?student_id=<uuid>  — teacher viewing one student's grade
  (no param)          — student views their own grade
"""

from django.db.models import Avg, Sum, F, FloatField, ExpressionWrapper
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@action(detail=True, methods=['get'], url_path='final-grade', permission_classes=[IsAuthenticated])
def final_grade(self, request, pk=None):
    course = self.get_object()

    # ── Resolve which student we're computing for ─────────────────────────────
    if request.user.is_student:
        student = request.user
    else:
        student_id = request.query_params.get('student_id')
        if not student_id:
            # Teacher: return all students enrolled in this course
            return _all_students_final_grades(course)
        from apps.users.models import User
        try:
            student = User.objects.get(pk=student_id)
        except User.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=404)

    from apps.exams.models import ExamAttempt
    from apps.assignments.models import Submission, Assignment

    # ── Exam component ────────────────────────────────────────────────────────
    exam            = getattr(course, 'exam', None)
    exam_weight     = exam.exam_weight     if exam else 70
    assignment_weight = exam.assignment_weight if exam else 30
    passing_score   = exam.passing_score   if exam else 60

    best_attempt = None
    exam_score   = None
    submitted_count      = 0
    retakes_remaining    = None

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

    # ── Assignment component ──────────────────────────────────────────────────
    # Percentage score for each graded submission: (score / max_score) * 100
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

    # ── Weighted final grade ──────────────────────────────────────────────────
    final_grade_value = None
    if exam_score is not None and assignment_avg is not None:
        final_grade_value = round(
            exam_score * (exam_weight / 100) + assignment_avg * (assignment_weight / 100), 1
        )
    elif exam_score is not None:
        # No graded assignments yet → weight exam score proportionally
        final_grade_value = round(exam_score, 1)
    elif assignment_avg is not None:
        # No exam yet → use assignment avg only
        final_grade_value = round(assignment_avg, 1)

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


def _all_students_final_grades(course):
    """
    Teacher shortcut: returns final grades for every enrolled student.
    Lighter query — no per-question breakdown.
    """
    from apps.exams.models import ExamAttempt
    from apps.assignments.models import Submission, Assignment
    from django.db.models import ExpressionWrapper, F, FloatField, Max

    exam = getattr(course, 'exam', None)
    exam_weight       = exam.exam_weight       if exam else 70
    assignment_weight = exam.assignment_weight if exam else 30
    passing_score     = exam.passing_score     if exam else 60
    total_assignments = Assignment.objects.filter(lesson__course=course).count()

    enrollments = course.enrollments.select_related('student').all()
    results = []

    for enroll in enrollments:
        student = enroll.student

        # Best exam score
        best = (
            ExamAttempt.objects
            .filter(student=student, exam=exam, is_submitted=True)
            .aggregate(best=Max('score'))['best']
            if exam else None
        )

        # Assignment average
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

        # Weighted total
        if best is not None and avg_asgn is not None:
            final = round(best * (exam_weight / 100) + avg_asgn * (assignment_weight / 100), 1)
        elif best is not None:
            final = round(best, 1)
        elif avg_asgn is not None:
            final = round(avg_asgn, 1)
        else:
            final = None

        results.append({
            'student_id':       str(student.pk),
            'student_name':     student.name,
            'student_email':    student.email,
            'exam_score':       best,
            'assignment_avg':   avg_asgn,
            'graded_submissions': graded.count(),
            'total_assignments':  total_assignments,
            'final_grade':      final,
            'passed':           (final >= passing_score) if final is not None else None,
        })

    return Response({
        'exam_weight':       exam_weight,
        'assignment_weight': assignment_weight,
        'passing_score':     passing_score,
        'students':          results,
    })
