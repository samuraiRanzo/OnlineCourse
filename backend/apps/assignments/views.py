from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from django.utils import timezone

from apps.users.permissions import IsAdmin
from .models import Assignment, Submission
from .serializers import AssignmentSerializer, SubmissionSerializer, GradeSerializer


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    Teacher: create/edit/delete assignments per lesson.
    Student: read-only, filtered to their enrolled courses.

    Query params:
      ?lesson=<uuid>  — filter by lesson (used by student LessonView)
      ?course=<uuid>  — filter by course (used by teacher CourseDetailView)
    """
    serializer_class = AssignmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Assignment.objects.select_related('lesson__course').prefetch_related(
            'submissions__student'
        )

        lesson_id = self.request.query_params.get('lesson')
        course_id = self.request.query_params.get('course')

        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        if course_id:
            qs = qs.filter(lesson__course_id=course_id)

        if self.request.user.is_student:
            enrolled_ids = self.request.user.enrollments.values_list('course_id', flat=True)
            qs = qs.filter(
                lesson__course_id__in=enrolled_ids,
                lesson__status='published',
                lesson__course__status='published',
            )

        return qs


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    Students POST to submit. Admin GETs to review and PATCHes /grade/ to score.

    POST /api/submissions/  { assignment: uuid, text_answer?: str, file?: File }
      → upserts: student can resubmit until graded.

    PATCH /api/submissions/{id}/grade/  { score: int, feedback?: str }
      → admin only; also fires an in-app notification to the student.

    Query params (admin only):
      ?assignment=<uuid>  — all submissions for one assignment
      ?student=<uuid>     — all submissions by one student
    """
    serializer_class = SubmissionSerializer
    parser_classes   = [MultiPartParser, JSONParser]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_permissions(self):
        if self.action == 'grade':
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Submission.objects.select_related(
            'student', 'assignment__lesson__course'
        )
        if self.request.user.is_student:
            return qs.filter(student=self.request.user)

        # Admin — optional filters
        assignment_id = self.request.query_params.get('assignment')
        student_id    = self.request.query_params.get('student')
        if assignment_id:
            qs = qs.filter(assignment_id=assignment_id)
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def create(self, request, *args, **kwargs):
        """
        Student submits or resubmits an assignment.
        Resubmission is allowed until the teacher grades it.
        """
        assignment_id = request.data.get('assignment')
        if not assignment_id:
            return Response({'detail': 'assignment is required.'}, status=400)

        try:
            assignment = Assignment.objects.select_related('lesson__course').get(pk=assignment_id)
        except Assignment.DoesNotExist:
            return Response({'detail': 'Assignment not found.'}, status=404)

        # Confirm student is enrolled
        if not request.user.enrollments.filter(course=assignment.lesson.course).exists():
            return Response({'detail': 'Not enrolled in this course.'}, status=403)

        text_answer = request.data.get('text_answer', '')
        file        = request.FILES.get('file')

        if not (text_answer and text_answer.strip()) and not file:
            return Response(
                {'detail': 'Submit at least a text answer or a file.'},
                status=400,
            )

        obj, created = Submission.objects.get_or_create(
            student=request.user,
            assignment=assignment,
            defaults={'text_answer': '', 'score': None},
        )

        # Block resubmission after grading
        if not created and obj.score is not None:
            return Response(
                {'detail': 'Cannot resubmit — this assignment has already been graded.'},
                status=403,
            )

        obj.text_answer = text_answer or ''
        if file:
            obj.file = file
        obj.save()

        return Response(
            SubmissionSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin], url_path='grade')
    def grade(self, request, pk=None):
        """
        Admin grades a submission.
        PATCH { score: int, feedback?: str }
        Fires an in-app notification to the student on success.
        """
        submission = self.get_object()
        serializer = GradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        score    = serializer.validated_data['score']
        feedback = serializer.validated_data['feedback']
        max_score = submission.assignment.max_score

        if score > max_score:
            return Response(
                {'detail': f'Score cannot exceed max_score of {max_score}.'},
                status=400,
            )

        submission.score     = score
        submission.feedback  = feedback
        submission.graded_at = timezone.now()
        submission.save(update_fields=['score', 'feedback', 'graded_at'])

        # ── In-app notification ───────────────────────────────────────────────
        try:
            from apps.notifications.models import Notification
            course = submission.assignment.lesson.course
            Notification.objects.create(
                recipient=submission.student,
                type=Notification.Type.EXAM_GRADED,
                title=f'Assignment graded — {submission.assignment.title}',
                body=(
                    f'Score: {score}/{max_score}'
                    + (f' · {feedback[:80]}' if feedback else '')
                ),
                link=f'/my-courses/{course.id}/lessons/{submission.assignment.lesson_id}',
            )
        except Exception:
            pass  # Notification failure must never break the grading response

        # ── Check if grading completes any certificate conditions ─────────────
        try:
            from apps.certificates.utils import maybe_issue_certificate
            maybe_issue_certificate(submission.student, submission.assignment.lesson.course)
        except Exception:
            pass

        return Response(SubmissionSerializer(submission, context={'request': request}).data)
