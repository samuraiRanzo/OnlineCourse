from rest_framework import serializers
from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name',  read_only=True)
    student_type = serializers.CharField(source='student.student_type', read_only=True)
    course_title = serializers.CharField(source='course.title',  read_only=True)

    class Meta:
        model  = Certificate
        fields = [
            'id', 'student', 'student_name', 'student_type',
            'course', 'course_title', 'cert_code', 'issued_at',
        ]
        read_only_fields = ['id', 'cert_code', 'issued_at']
