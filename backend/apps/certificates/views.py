from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdmin
from .models import Certificate
from .serializers import CertificateSerializer


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Certificates are issued automatically — no POST endpoint needed.
    Admin sees all. Students see only their own.
    """
    serializer_class = CertificateSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Certificate.objects.select_related('student', 'course')
        if self.request.user.is_student:
            return qs.filter(student=self.request.user)
        # Admin filters
        student_id = self.request.query_params.get('student')
        course_id  = self.request.query_params.get('course')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs
