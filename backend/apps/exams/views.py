from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdmin
from .models import Exam, Question, ExamResult
from .serializers import (
    ExamSerializer, ExamWriteSerializer, QuestionSerializer,
    SubmitExamSerializer, ExamResultSerializer, GradeOpenAnswerSerializer,
)


def _calculate_score(exam, answers: dict) -> int:
    """Calculate MCQ score as a percentage. Open questions are excluded."""
    mcq_questions = exam.questions.filter(type='mcq')
    total = mcq_questions.count()
    if total == 0:
        return 100
    correct = 0
    for q in mcq_questions:
        idx        = str(q.order)
        user_ans   = answers.get(idx)
        if user_ans is not None and int(user_ans) == q.correct_index:
            correct += 1
    return round((correct / total) * 100)


class ExamViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ExamWriteSerializer
        return ExamSerializer

    def get_queryset(self):
        qs = Exam.objects.select_related('course').prefetch_related('questions')
        if self.request.user.is_student:
            enrolled_ids = self.request.user.enrollments.values_list('course_id', flat=True)
            qs = qs.filter(course_id__in=enrolled_ids)
        return qs


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Question.objects.filter(exam_id=self.kwargs['exam_pk']).order_by('order')

    def perform_create(self, serializer):
        exam       = Exam.objects.get(pk=self.kwargs['exam_pk'])
        last_order = exam.questions.count()
        serializer.save(exam=exam, order=last_order)


class ExamResultViewSet(viewsets.ModelViewSet):
    serializer_class = ExamResultSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = ExamResult.objects.select_related('exam__course', 'student')
        if self.request.user.is_student:
            return qs.filter(student=self.request.user)
        # Admin can filter by student or exam
        student_id = self.request.query_params.get('student')
        exam_id    = self.request.query_params.get('exam')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if exam_id:
            qs = qs.filter(exam_id=exam_id)
        return qs

    def create(self, request, *args, **kwargs):
        """
        Student submits exam answers.
        POST /api/exams/results/ { "exam": <uuid>, "answers": { "0": 2, "1": "text" } }
        Score is calculated server-side. Attempt number is auto-incremented.
        Blocked if the student has used all allowed retakes.
        """
        serializer = SubmitExamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam_id = request.data.get('exam')
        try:
            exam = Exam.objects.prefetch_related('questions').get(pk=exam_id)
        except Exam.DoesNotExist:
            return Response({'detail': 'Exam not found.'}, status=404)

        # Verify enrollment
        if not request.user.enrollments.filter(course=exam.course).exists():
            return Response({'detail': 'Not enrolled in this course.'}, status=403)

        # Enforce retake limit (0 = unlimited)
        attempts_so_far = ExamResult.objects.filter(
            exam=exam, student=request.user
        ).count()

        if exam.max_retakes > 0 and attempts_so_far >= exam.max_retakes:
            return Response(
                {
                    'detail': f'Retake limit reached. '
                              f'This exam allows {exam.max_retakes} attempt(s). '
                              f'You have used {attempts_so_far}.',
                    'attempts_used': attempts_so_far,
                    'max_retakes':   exam.max_retakes,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        answers = serializer.validated_data['answers']
        score   = _calculate_score(exam, answers)
        attempt = attempts_so_far + 1

        result = ExamResult.objects.create(
            exam=exam,
            student=request.user,
            score=score,
            answers=answers,
            attempt=attempt,
        )

        from apps.certificates.utils import maybe_issue_certificate
        maybe_issue_certificate(request.user, exam.course)

        return Response(
            ExamResultSerializer(result, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin],
            url_path='grade-open')
    def grade_open(self, request, pk=None):
        """
        Admin grades an open answer.
        PATCH { "question_index": 2, "grade": "Pass" }
        """
        result     = self.get_object()
        serializer = GradeOpenAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idx   = str(serializer.validated_data['question_index'])
        grade = serializer.validated_data['grade']

        if grade:
            result.open_grades[idx] = grade
        else:
            result.open_grades.pop(idx, None)
        result.save(update_fields=['open_grades'])

        return Response(ExamResultSerializer(result).data)
