import random
import string
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdmin
from apps.courses.models import Enrollment
from .models import Session, Attendance
from .serializers import SessionSerializer, AttendanceSerializer, CheckInSerializer
from .utils import get_attendance_stats


def generate_code():
    """Generate a unique 6-char uppercase alphanumeric code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Session.objects.filter(code=code).exists():
            return code


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'toggle_attendance']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs         = Session.objects.select_related('course').prefetch_related('attendances')
        course_id  = self.request.query_params.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(code=generate_code())

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin],
            url_path='toggle-attendance')
    def toggle_attendance(self, request, pk=None):
        """
        Admin manually marks or unmarks a student present.
        POST { "student_id": "uuid" }
        """
        session    = self.get_object()
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required.'}, status=400)

        att, created = Attendance.objects.get_or_create(
            session=session, student_id=student_id
        )
        if not created:
            att.delete()
            return Response({'status': 'removed', 'student_id': str(student_id)})
        return Response({'status': 'added', 'student_id': str(student_id)},
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated],
            url_path='stats')
    def stats(self, request):
        """
        Returns attendance % for a student in a course.
        GET /api/attendance/sessions/stats/?student=<id>&course=<id>
        """
        student_id = request.query_params.get('student', str(request.user.id))
        course_id  = request.query_params.get('course')
        if not course_id:
            return Response({'detail': 'course param required.'}, status=400)
        return Response(get_attendance_stats(student_id, course_id))


class CheckInView(viewsets.ViewSet):
    """Student-facing: POST { "code": "ABC123" } to mark themselves present."""
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']

        try:
            session = Session.objects.select_related('course').get(code=code)
        except Session.DoesNotExist:
            return Response({'detail': 'Invalid code.'}, status=status.HTTP_404_NOT_FOUND)

        # Confirm the student is enrolled in the course this session belongs to
        enrolled = Enrollment.objects.filter(
            student=request.user, course=session.course
        ).exists()
        if not enrolled:
            return Response(
                {'detail': 'You are not enrolled in this course.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        att, created = Attendance.objects.get_or_create(
            session=session, student=request.user
        )
        if not created:
            return Response(
                {'detail': 'Already checked in.', 'already_checked_in': True},
                status=status.HTTP_200_OK,
            )

        stats = get_attendance_stats(str(request.user.id), str(session.course_id))
        return Response({
            'detail':            'Attendance recorded.',
            'already_checked_in': False,
            'session':           SessionSerializer(session).data,
            'attendance_stats':  stats,
        }, status=status.HTTP_201_CREATED)
