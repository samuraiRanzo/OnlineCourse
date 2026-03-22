from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg, Max, F, FloatField, ExpressionWrapper

from apps.users.permissions import IsAdmin
from .models import (
    Course, Lesson, Enrollment, LessonCompletion,
    LessonQuestion, LessonAnswer, LessonAttachment, LessonNote,
)
from .serializers import (
    CourseSerializer, CourseListSerializer, LessonSerializer,
    EnrollmentSerializer, LessonCompletionSerializer,
    LessonQuestionSerializer, LessonAnswerSerializer,
    LessonAttachmentSerializer, LessonNoteSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related('lessons').all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'reorder_lessons', 'publish', 'unpublish']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        return CourseListSerializer if self.action == 'list' else CourseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_student:
            enrolled_ids = self.request.user.enrollments.values_list('course_id', flat=True)
            qs = qs.filter(id__in=enrolled_ids, status='published')
        return qs

    # ── Publish / Unpublish ───────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        course = self.get_object()
        if course.status == 'published':
            return Response({'detail': 'Course is already published.'}, status=400)
        course.status = 'published'
        if not course.published_at:
            course.published_at = timezone.now()
        course.save(update_fields=['status', 'published_at'])
        return Response(CourseSerializer(course, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='unpublish')
    def unpublish(self, request, pk=None):
        course = self.get_object()
        if course.status == 'draft':
            return Response({'detail': 'Course is already a draft.'}, status=400)
        course.status = 'draft'
        course.save(update_fields=['status'])
        return Response(CourseSerializer(course, context={'request': request}).data)

    # ── Reorder lessons ───────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin], url_path='reorder-lessons')
    def reorder_lessons(self, request, pk=None):
        course  = self.get_object()
        ordered = request.data.get('order', [])
        if not isinstance(ordered, list):
            return Response({'detail': 'order must be a list of lesson IDs.'}, status=400)
        lessons = {str(l.id): l for l in course.lessons.all()}
        for idx, lid in enumerate(ordered):
            if lid in lessons:
                lessons[lid].order = idx
        Lesson.objects.bulk_update(lessons.values(), ['order'])
        return Response(LessonSerializer(course.lessons.order_by('order'), many=True).data)

    # ── Q&A Inbox ─────────────────────────────────────────────────────────────

    @action(
        detail=True, methods=['get'],
        permission_classes=[IsAdmin],
        url_path='all-questions',
    )
    def all_questions(self, request, pk=None):
        """
        GET /api/courses/{id}/all-questions/
        Returns all questions across every lesson in the course.
        Optional: ?is_resolved=true|false
        """
        course = self.get_object()
        qs = (
            LessonQuestion.objects
            .filter(lesson__course=course)
            .select_related('lesson', 'author')
            .prefetch_related('answers__author')
            .order_by('is_resolved', '-created_at')
        )
        is_resolved_param = request.query_params.get('is_resolved')
        if is_resolved_param is not None:
            qs = qs.filter(is_resolved=is_resolved_param.lower() == 'true')
        serializer = LessonQuestionSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # ── Analytics ─────────────────────────────────────────────────────────────

    @action(
        detail=True, methods=['get'],
        permission_classes=[IsAdmin],
        url_path='analytics',
    )
    def analytics(self, request, pk=None):
        """
        GET /api/courses/{id}/analytics/
        Aggregated course metrics for the teacher dashboard.
        Uses ExamAttempt (current model) — NOT the old ExamResult.
        """
        course = self.get_object()

        # ── Enrollment breakdown ──────────────────────────────────────────────
        enrollments    = course.enrollments.select_related('student').all()
        enrolled_count = enrollments.count()
        online_count   = enrollments.filter(student__student_type='online').count()
        onsite_count   = enrollments.filter(student__student_type='onsite').count()

        # ── Exam metrics ──────────────────────────────────────────────────────
        avg_score          = None
        pass_rate          = 0
        score_distribution = [0] * 10
        attempts_over_time = []
        student_scores     = []

        try:
            from apps.exams.models import ExamAttempt  # current model name
            exam     = course.exam       # raises AttributeError if no exam yet
            attempts = ExamAttempt.objects.filter(
                exam=exam, is_submitted=True
            ).select_related('student')

            if attempts.exists():
                agg       = attempts.aggregate(avg=Avg('score'))
                avg_score = round(agg['avg'], 1) if agg['avg'] is not None else None

                # 10-bucket score distribution (0-9%, 10-19%, …, 90-100%)
                for score in attempts.values_list('score', flat=True):
                    if score is not None:
                        bucket = min(int(score / 10), 9)
                        score_distribution[bucket] += 1

                # Attempts submitted per calendar day
                from django.db.models.functions import TruncDate
                daily = (
                    attempts
                    .annotate(day=TruncDate('submitted_at'))
                    .values('day')
                    .annotate(count=Count('id'))
                    .order_by('day')
                )
                attempts_over_time = [
                    {'date': str(row['day']), 'count': row['count']}
                    for row in daily
                ]

                # Latest attempt per enrolled student → pass rate + per-student table
                enrolled_ids = enrollments.values_list('student_id', flat=True)
                seen = {}
                for a in attempts.filter(student_id__in=enrolled_ids).order_by('-submitted_at'):
                    if a.student_id not in seen:
                        seen[a.student_id] = a
                latest       = list(seen.values())
                passing      = exam.passing_score
                passed_count = sum(1 for a in latest if a.score is not None and a.score >= passing)
                pass_rate    = round((passed_count / len(latest) * 100)) if latest else 0
                student_scores = [
                    {'name': a.student.name, 'score': a.score, 'passed': (a.score or 0) >= passing}
                    for a in sorted(latest, key=lambda a: a.score or 0, reverse=True)
                ]
        except Exception:
            # Course has no exam yet — defaults (zeros/nulls) apply
            pass

        # ── Lesson completion rates ───────────────────────────────────────────
        lessons           = course.lessons.filter(status='published').order_by('order')
        lesson_completion = []
        if enrolled_count > 0:
            for lesson in lessons:
                completed = LessonCompletion.objects.filter(
                    lesson=lesson,
                    enrollment__course=course,
                ).count()
                lesson_completion.append({
                    'lesson_title': lesson.title,
                    'completed':    completed,
                    'total':        enrolled_count,
                    'pct':          round((completed / enrolled_count) * 100),
                })

        # ── Attendance per session ────────────────────────────────────────────
        attendance_sessions = []
        try:
            from apps.attendance.models import Session as AttSession
            att_sessions    = AttSession.objects.filter(course=course).order_by('date')
            reference_total = onsite_count if onsite_count > 0 else enrolled_count
            for session in att_sessions:
                attendance_sessions.append({
                    'label':    session.label,
                    'date':     str(session.date),
                    'attended': session.attendances.count(),
                    'total':    reference_total,
                })
        except Exception:
            pass

        return Response({
            'enrolled_count':      enrolled_count,
            'online_count':        online_count,
            'onsite_count':        onsite_count,
            'avg_score':           avg_score,
            'pass_rate':           pass_rate,
            'score_distribution':  score_distribution,
            'attempts_over_time':  attempts_over_time,
            'lesson_completion':   lesson_completion,
            'attendance_sessions': attendance_sessions,
            'student_scores':      student_scores,
        })

    # ── Final Grade (weighted exam + assignments) ──────────────────────────────

    @action(
        detail=True, methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='final-grade',
    )
    def final_grade(self, request, pk=None):
        """
        GET /api/courses/{id}/final-grade/
          Student  → their own grade
          Teacher  → all students (no param)
          Teacher  → one student (?student_id=<uuid>)

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

        return Response(_student_final_grade(course, student))


# ── Final grade helpers ───────────────────────────────────────────────────────

def _student_final_grade(course, student):
    from apps.exams.models import ExamAttempt
    from apps.assignments.models import Submission, Assignment

    exam              = getattr(course, 'exam', None)
    exam_weight       = exam.exam_weight       if exam else 70
    assignment_weight = exam.assignment_weight if exam else 30
    passing_score     = exam.passing_score     if exam else 60

    # Exam — best submitted attempt
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

    # Assignments — average % score across graded submissions
    total_assignments = Assignment.objects.filter(lesson__course=course).count()
    graded_subs = Submission.objects.filter(
        student=student,
        assignment__lesson__course=course,
        score__isnull=False,
    ).annotate(
        pct=ExpressionWrapper(
            F('score') * 100.0 / F('assignment__max_score'),
            output_field=FloatField(),
        )
    )
    graded_count   = graded_subs.count()
    assignment_avg = graded_subs.aggregate(avg=Avg('pct'))['avg']
    if assignment_avg is not None:
        assignment_avg = round(assignment_avg, 1)

    # Weighted final
    if exam_score is not None and assignment_avg is not None:
        final = round(exam_score * (exam_weight / 100) + assignment_avg * (assignment_weight / 100), 1)
    elif exam_score is not None:
        final = round(exam_score, 1)
    elif assignment_avg is not None:
        final = round(assignment_avg, 1)
    else:
        final = None

    passed = (final >= passing_score) if final is not None else None

    return {
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
        'final_grade':         final,
        'passed':              passed,
    }


def _all_students_final_grades(course):
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
            final = round(best * (exam_weight / 100) + avg_asgn * (assignment_weight / 100), 1)
        elif best is not None:
            final = round(best, 1)
        elif avg_asgn is not None:
            final = round(avg_asgn, 1)
        else:
            final = None

        results.append({
            'student_id':          str(student.pk),
            'student_name':        student.name,
            'student_email':       student.email,
            'student_type':        student.student_type,
            'exam_score':          best,
            'assignment_avg':      avg_asgn,
            'graded_submissions':  graded.count(),
            'total_assignments':   total_assignments,
            'final_grade':         final,
            'passed':              (final >= passing_score) if final is not None else None,
        })

    from rest_framework.response import Response
    return Response({
        'exam_weight':       exam_weight,
        'assignment_weight': assignment_weight,
        'passing_score':     passing_score,
        'students':          results,
    })


# ── Lessons ───────────────────────────────────────────────────────────────────

class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    parser_classes   = [
        __import__('rest_framework.parsers', fromlist=['MultiPartParser']).MultiPartParser,
        __import__('rest_framework.parsers', fromlist=['JSONParser']).JSONParser,
    ]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'publish', 'unpublish']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Lesson.objects.filter(course_id=self.kwargs['course_pk']).order_by('order')
        if self.request.user.is_student:
            qs = qs.filter(status='published')
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        course     = Course.objects.get(pk=self.kwargs['course_pk'])
        last_order = course.lessons.count()
        lesson     = serializer.save(course=course, order=last_order)
        if lesson.type == 'video' and lesson.video_file:
            from .tasks import transcode_to_hls
            transcode_to_hls.delay(str(lesson.id))

    def perform_update(self, serializer):
        lesson = serializer.save()
        if lesson.type == 'video' and 'video_file' in self.request.FILES:
            lesson.hls_ready = False
            lesson.hls_path  = ''
            lesson.save(update_fields=['hls_ready', 'hls_path'])
            from .tasks import transcode_to_hls
            transcode_to_hls.delay(str(lesson.id))

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, course_pk=None, pk=None):
        lesson = self.get_object()
        if lesson.status == 'published':
            return Response({'detail': 'Lesson is already published.'}, status=400)
        lesson.status = 'published'
        lesson.save(update_fields=['status'])
        return Response(LessonSerializer(lesson, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='unpublish')
    def unpublish(self, request, course_pk=None, pk=None):
        lesson = self.get_object()
        if lesson.status == 'draft':
            return Response({'detail': 'Lesson is already a draft.'}, status=400)
        lesson.status = 'draft'
        lesson.save(update_fields=['status'])
        return Response(LessonSerializer(lesson, context={'request': request}).data)

    @action(
        detail=True, methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
        url_path='note',
    )
    def note(self, request, course_pk=None, pk=None):
        """
        GET  → return the student's note for this lesson (creates blank if absent)
        PATCH { body: "..." } → upsert the note body
        Admin-blocked — notes are for students only.
        """
        if not request.user.is_student:
            return Response(
                {'detail': 'Notes are for students only.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        lesson      = self.get_object()
        note_obj, _ = LessonNote.objects.get_or_create(
            student=request.user, lesson=lesson, defaults={'body': ''},
        )
        if request.method == 'GET':
            return Response(LessonNoteSerializer(note_obj).data)
        serializer = LessonNoteSerializer(note_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── Enrollments ───────────────────────────────────────────────────────────────

class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Enrollment.objects.select_related('student', 'course').prefetch_related('completions')
        if self.request.user.is_student:
            return qs.filter(student=self.request.user)
        student_id = self.request.query_params.get('student')
        course_id  = self.request.query_params.get('course')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class LessonCompletionViewSet(viewsets.ModelViewSet):
    serializer_class   = LessonCompletionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = LessonCompletion.objects.select_related('enrollment', 'lesson')
        if self.request.user.is_student:
            return qs.filter(enrollment__student=self.request.user)
        return qs

    def create(self, request, *args, **kwargs):
        obj, created = LessonCompletion.objects.get_or_create(
            enrollment_id=request.data.get('enrollment'),
            lesson_id=request.data.get('lesson'),
        )
        return Response(
            self.get_serializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ── Q&A ───────────────────────────────────────────────────────────────────────

class LessonQuestionViewSet(viewsets.ModelViewSet):
    serializer_class  = LessonQuestionSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return LessonQuestion.objects.filter(
            lesson_id=self.kwargs['lesson_pk']
        ).select_related('author').prefetch_related('answers__author')

    def get_permissions(self):
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        lesson = Lesson.objects.get(pk=self.kwargs['lesson_pk'])
        serializer.save(author=self.request.user, lesson=lesson)

    def partial_update(self, request, *args, **kwargs):
        question = self.get_object()
        if request.user.is_student and question.author != request.user:
            return Response({'detail': 'You can only edit your own questions.'}, status=403)
        if request.user.is_student and 'is_resolved' in request.data:
            return Response({'detail': 'Only the teacher can resolve questions.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        if request.user.is_student and question.author != request.user:
            return Response({'detail': 'You can only delete your own questions.'}, status=403)
        return super().destroy(request, *args, **kwargs)


class LessonAnswerViewSet(viewsets.ModelViewSet):
    serializer_class  = LessonAnswerSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return LessonAnswer.objects.filter(
            question_id=self.kwargs['question_pk']
        ).select_related('author')

    def get_permissions(self):
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        question = LessonQuestion.objects.get(pk=self.kwargs['question_pk'])
        serializer.save(author=self.request.user, question=question)

    def partial_update(self, request, *args, **kwargs):
        answer = self.get_object()
        if answer.author != request.user:
            return Response({'detail': 'You can only edit your own answers.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        answer = self.get_object()
        if request.user.is_student and answer.author != request.user:
            return Response({'detail': 'You can only delete your own answers.'}, status=403)
        return super().destroy(request, *args, **kwargs)


# ── Attachments ───────────────────────────────────────────────────────────────

class LessonAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class  = LessonAttachmentSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    parser_classes    = [
        __import__('rest_framework.parsers', fromlist=['MultiPartParser']).MultiPartParser,
        __import__('rest_framework.parsers', fromlist=['JSONParser']).JSONParser,
    ]

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdmin()]
        if self.action == 'stream':
            from rest_framework.permissions import AllowAny
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return LessonAttachment.objects.filter(lesson_id=self.kwargs['lesson_pk'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        lesson   = Lesson.objects.get(pk=self.kwargs['lesson_pk'])
        uploaded = self.request.FILES.get('file')
        if not uploaded:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'file': 'No file was uploaded.'})
        name      = self.request.data.get('name', '').strip() or uploaded.name
        file_size = uploaded.size
        serializer.save(lesson=lesson, name=name, file_size=file_size, file=uploaded)

    @action(detail=True, methods=['get'], url_path='stream')
    def stream(self, request, **kwargs):
        from django.http import FileResponse, Http404
        import mimetypes
        attachment = self.get_object()
        if not attachment.file.name:
            raise Http404
        try:
            f = attachment.file.open('rb')
        except (FileNotFoundError, OSError, ValueError):
            raise Http404
        mime, _ = mimetypes.guess_type(attachment.name)
        response = FileResponse(f, content_type=mime or 'application/octet-stream')
        safe_name = attachment.name.replace('"', '\\"')
        response['Content-Disposition'] = f'inline; filename="{safe_name}"'
        return response
