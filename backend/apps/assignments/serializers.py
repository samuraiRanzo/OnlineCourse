from rest_framework import serializers
from .models import Assignment, Submission


class SubmissionSerializer(serializers.ModelSerializer):
    student_name  = serializers.CharField(source='student.name',         read_only=True)
    student_email = serializers.CharField(source='student.email',        read_only=True)
    student_type  = serializers.CharField(source='student.student_type', read_only=True)
    is_graded     = serializers.BooleanField(read_only=True)
    # file is write-only on upload; file_url exposes the download link
    file_url      = serializers.SerializerMethodField()

    class Meta:
        model  = Submission
        fields = [
            'id', 'assignment',
            'student', 'student_name', 'student_email', 'student_type',
            'file', 'file_url', 'text_answer',
            'score', 'feedback', 'is_graded',
            'submitted_at', 'updated_at', 'graded_at',
        ]
        read_only_fields = [
            'id', 'student', 'submitted_at', 'updated_at', 'graded_at', 'is_graded',
        ]
        extra_kwargs = {
            # clients upload via 'file'; they download via 'file_url'
            'file': {'write_only': True, 'required': False},
            'score':    {'read_only': True},
            'feedback': {'read_only': True},
        }

    def get_file_url(self, obj):
        if not obj.file or not obj.file.name:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class AssignmentSerializer(serializers.ModelSerializer):
    lesson_title     = serializers.CharField(source='lesson.title',     read_only=True)
    course_id        = serializers.UUIDField(source='lesson.course_id', read_only=True)
    submission_count = serializers.IntegerField(source='submissions.count', read_only=True)
    # For students: their own submission embedded in the response (null if not submitted)
    my_submission    = serializers.SerializerMethodField()

    class Meta:
        model  = Assignment
        fields = [
            'id', 'lesson', 'lesson_title', 'course_id',
            'title', 'description', 'due_date', 'max_score',
            'created_at', 'submission_count', 'my_submission',
        ]
        read_only_fields = ['id', 'created_at', 'lesson_title', 'course_id', 'submission_count']

    def get_my_submission(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or not request.user.is_student:
            return None
        sub = obj.submissions.filter(student=request.user).first()
        if sub:
            return SubmissionSerializer(sub, context=self.context).data
        return None


class GradeSerializer(serializers.Serializer):
    score    = serializers.IntegerField(min_value=0)
    feedback = serializers.CharField(allow_blank=True, default='')
