from django.db.models import Sum, Avg, F, FloatField, ExpressionWrapper
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdmin
from .models import Exam, ExamAttempt, QuestionResponse
from .serializers import (
    ExamSerializer,
    ExamForStudentSerializer,
    ExamAttemptSerializer,
    ExamAttemptTeacherSerializer,
    QuestionResponseTeacherSerializer,
    GradeResponseSerializer,
)


class ExamViewSet(viewsets.ModelViewSet):
    """
    Endpoints:
      GET    /api/exams/?course=<id>         → teacher gets full exam (with correct_index)
      GET    /api/exams/<id>/for-student/    → student gets safe exam (no correct_index)
      POST   /api/exams/<id>/start/          → create or resume an in-progress attempt
      POST   /api/exams/<id>/submit/         → submit answers, auto-grade MCQ
      GET    /api/exams/<id>/my-attempts/    → student's own attempts with results
      GET    /api/exams/<id>/all-attempts/   → teacher: all students' attempts
      POST/PATCH /api/exams/ or /<id>/      → teacher creates / updates exam
    """
    queryset = Exam.objects.select_related('course').all()

    def get_serializer_class(self):
        if self.request.user.is_student:
            return ExamForStudentSerializer
        return ExamSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Exam.objects.select_related('course')
        course_id = self.request.query_params.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    # ── Student: get exam without correct answers ─────────────────────────────

    @action(detail=True, methods=['get'], url_path='for-student')
    def for_student(self, request, pk=None):
        exam = self.get_object()
        return Response(ExamForStudentSerializer(exam).data)

    # ── Start / resume attempt ────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='start', permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        """
        POST /api/exams/<id>/start/

        1. If student has an in-progress attempt, return it (resume).
        2. Otherwise create a new attempt — respecting max_retakes.
        """
        if not request.user.is_student:
            return Response({'detail': 'Only students can start an exam.'}, status=403)

        exam = self.get_object()

        # Check enrollment
        if not request.user.enrollments.filter(course=exam.course).exists():
            return Response({'detail': 'Not enrolled in this course.'}, status=403)

        # Resume in-progress attempt
        in_progress = ExamAttempt.objects.filter(
            student=request.user, exam=exam, is_submitted=False
        ).first()
        if in_progress:
            return Response(ExamAttemptSerializer(in_progress).data)

        # Check retake limit
        submitted_count = ExamAttempt.objects.filter(
            student=request.user, exam=exam, is_submitted=True
        ).count()
        if exam.max_retakes > 0 and submitted_count >= exam.max_retakes:
            return Response(
                {'detail': f'No retakes remaining. You have used {submitted_count}/{exam.max_retakes} attempt(s).'},
                status=403,
            )

        attempt = ExamAttempt.objects.create(
            student=request.user,
            exam=exam,
            time_limit_snapshot=exam.time_limit_minutes,
        )
        return Response(ExamAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)

    # ── Submit ────────────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='submit', permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """
        POST /api/exams/<id>/submit/
        Body:
          {
            "attempt_id": "<uuid>",
            "auto_submitted": false,
            "responses": [
              {"question_index": 0, "selected_index": 2},
              {"question_index": 1, "text_answer": "My open answer"}
            ]
          }

        MCQ questions → auto-graded immediately.
        Open questions → points_earned = null (awaiting teacher grade).
        Attempt.score  → MCQ points / total possible * 100.
                         Recomputed when teacher grades open questions.
        """
        if not request.user.is_student:
            return Response({'detail': 'Only students can submit.'}, status=403)

        exam = self.get_object()

        attempt_id = request.data.get('attempt_id')
        if not attempt_id:
            return Response({'detail': 'attempt_id is required.'}, status=400)

        try:
            attempt = ExamAttempt.objects.get(
                pk=attempt_id, student=request.user, exam=exam, is_submitted=False
            )
        except ExamAttempt.DoesNotExist:
            return Response(
                {'detail': 'Attempt not found or already submitted.'},
                status=404,
            )

        responses_data = request.data.get('responses', [])
        questions      = exam.questions
        num_questions  = len(questions)
        if num_questions == 0:
            return Response({'detail': 'This exam has no questions.'}, status=400)

        points_per_q = round(100.0 / num_questions, 4)
        has_open     = False

        for r in responses_data:
            qi   = r.get('question_index')
            if qi is None or qi >= num_questions:
                continue

            q     = questions[qi]
            qtype = q.get('type', 'open')

            if qtype == 'mcq':
                selected      = r.get('selected_index')
                correct       = q.get('correct_index')
                is_correct    = (selected is not None) and (selected == correct)
                points_earned = points_per_q if is_correct else 0.0

                QuestionResponse.objects.update_or_create(
                    attempt=attempt, question_index=qi,
                    defaults={
                        'question_type':  'mcq',
                        'question_text':  q.get('text', ''),
                        'options':        q.get('options', []),
                        'selected_index': selected,
                        'correct_index':  correct,
                        'max_points':     points_per_q,
                        'points_earned':  points_earned,
                        'is_correct':     is_correct,
                    }
                )
            else:  # open
                has_open = True
                QuestionResponse.objects.update_or_create(
                    attempt=attempt, question_index=qi,
                    defaults={
                        'question_type': 'open',
                        'question_text': q.get('text', ''),
                        'text_answer':   r.get('text_answer', ''),
                        'max_points':    points_per_q,
                        'points_earned': None,   # teacher grades later
                        'is_correct':    None,
                    }
                )

        # Compute score from MCQ only
        # Score = MCQ points earned / total possible points * 100
        # When teacher grades open Qs, this is recomputed in grade_response view.
        total_possible = points_per_q * num_questions  # always 100.0
        mcq_earned     = (
            QuestionResponse.objects
            .filter(attempt=attempt, question_type='mcq')
            .aggregate(s=Sum('points_earned'))['s'] or 0.0
        )
        score = round(mcq_earned / total_possible * 100, 1) if total_possible else 0

        attempt.score          = score
        attempt.is_submitted   = True
        attempt.auto_submitted = request.data.get('auto_submitted', False)
        attempt.submitted_at   = timezone.now()
        attempt.save(update_fields=['score', 'is_submitted', 'auto_submitted', 'submitted_at'])

        # Fire in-app notification if no open questions need grading
        if not has_open:
            _notify_exam_result(attempt)

        # Check certificate eligibility
        try:
            from apps.certificates.utils import maybe_issue_certificate
            maybe_issue_certificate(attempt.student, exam.course)
        except Exception:
            pass

        return Response(ExamAttemptSerializer(attempt).data)

    # ── My attempts ───────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='my-attempts', permission_classes=[IsAuthenticated])
    def my_attempts(self, request, pk=None):
        """GET /api/exams/<id>/my-attempts/"""
        if not request.user.is_student:
            return Response({'detail': 'Students only.'}, status=403)

        exam     = self.get_object()
        attempts = ExamAttempt.objects.filter(
            student=request.user, exam=exam, is_submitted=True
        ).prefetch_related('responses')

        submitted_count   = attempts.count()
        retakes_remaining = (
            max(0, exam.max_retakes - submitted_count)
            if exam.max_retakes > 0 else None
        )

        return Response({
            'exam_id':           str(exam.id),
            'exam_title':        exam.title,
            'max_retakes':       exam.max_retakes,
            'submitted_count':   submitted_count,
            'retakes_remaining': retakes_remaining,
            'passing_score':     exam.passing_score,
            'time_limit_minutes': exam.time_limit_minutes,
            'attempts':          ExamAttemptSerializer(attempts, many=True).data,
        })

    # ── All attempts (teacher) ────────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='all-attempts', permission_classes=[IsAdmin])
    def all_attempts(self, request, pk=None):
        """GET /api/exams/<id>/all-attempts/"""
        exam     = self.get_object()
        attempts = ExamAttempt.objects.filter(
            exam=exam, is_submitted=True
        ).select_related('student').prefetch_related('responses')

        return Response(ExamAttemptTeacherSerializer(attempts, many=True).data)


# ── QuestionResponse grading (teacher only) ───────────────────────────────────

class QuestionResponseViewSet(viewsets.GenericViewSet):
    """
    PATCH /api/exams/responses/<id>/grade/
    Teacher grades an open question response.
    Also recomputes the attempt's overall score.
    """
    queryset         = QuestionResponse.objects.select_related('attempt__exam__course', 'attempt__student')
    permission_classes = [IsAdmin]

    @action(detail=True, methods=['patch'], url_path='grade')
    def grade(self, request, pk=None):
        qr = self.get_object()

        if qr.question_type != QuestionResponse.TYPE_OPEN:
            return Response({'detail': 'Only open questions can be manually graded.'}, status=400)

        s = GradeResponseSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        points_earned    = s.validated_data['points_earned']
        teacher_feedback = s.validated_data['teacher_feedback']

        if points_earned > qr.max_points:
            return Response(
                {'detail': f'points_earned cannot exceed max_points ({qr.max_points}).'},
                status=400,
            )

        qr.points_earned     = points_earned
        qr.teacher_feedback  = teacher_feedback
        qr.graded_at         = timezone.now()
        qr.save(update_fields=['points_earned', 'teacher_feedback', 'graded_at'])

        # Recompute attempt score
        attempt = qr.attempt
        total_possible = (
            QuestionResponse.objects
            .filter(attempt=attempt)
            .aggregate(s=Sum('max_points'))['s'] or 0.0
        )
        total_earned = (
            QuestionResponse.objects
            .filter(attempt=attempt, points_earned__isnull=False)
            .aggregate(s=Sum('points_earned'))['s'] or 0.0
        )
        if total_possible:
            attempt.score = round(total_earned / total_possible * 100, 1)
            attempt.save(update_fields=['score'])

        # Fire notification only when ALL open questions are now graded
        still_pending = (
            QuestionResponse.objects
            .filter(attempt=attempt, question_type='open', points_earned__isnull=True)
            .count()
        )
        if still_pending == 0:
            _notify_exam_result(attempt)
            try:
                from apps.certificates.utils import maybe_issue_certificate
                maybe_issue_certificate(attempt.student, attempt.exam.course)
            except Exception:
                pass

        return Response(QuestionResponseTeacherSerializer(qr).data)


# ── Helper ────────────────────────────────────────────────────────────────────

def _notify_exam_result(attempt: ExamAttempt):
    """Fire an in-app notification to the student with their exam result."""
    try:
        from apps.notifications.models import Notification
        course = attempt.exam.course
        Notification.objects.create(
            recipient=attempt.student,
            type=Notification.Type.EXAM_GRADED,
            title=f'Exam result — {attempt.exam.title}',
            body=(
                f'Score: {attempt.score}% — '
                f'{"Passed ✓" if attempt.passed else "Not passed"}'
            ),
            link=f'/my-courses/{course.id}/exam',
        )
    except Exception:
        pass
