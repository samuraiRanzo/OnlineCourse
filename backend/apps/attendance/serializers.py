from rest_framework import serializers
from .models import Session, Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name  = serializers.CharField(source='student.name',  read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)

    class Meta:
        model  = Attendance
        fields = ['id', 'session', 'student', 'student_name', 'student_email', 'checked_in_at']
        read_only_fields = ['id', 'checked_in_at']


class SessionSerializer(serializers.ModelSerializer):
    course_title   = serializers.CharField(source='course.title', read_only=True)
    attendee_ids   = serializers.SerializerMethodField()
    attendee_count = serializers.IntegerField(source='attendances.count', read_only=True)

    class Meta:
        model  = Session
        fields = [
            'id', 'course', 'course_title', 'label', 'code',
            'date', 'created_at', 'attendee_ids', 'attendee_count',
        ]
        read_only_fields = ['id', 'code', 'created_at']

    def get_attendee_ids(self, obj):
        return list(obj.attendances.values_list('student_id', flat=True))


class CheckInSerializer(serializers.Serializer):
    """Student submits a 6-char code to mark themselves present."""
    code = serializers.CharField(max_length=6, min_length=6)

    def validate_code(self, value):
        return value.upper()
