from rest_framework import serializers
from .models import Exam, Question, ExamResult


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Question
        fields = ['id', 'type', 'text', 'options', 'correct_index', 'order']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Hide correct_index from students — only shown in result review
        request = self.context.get('request')
        if request and request.user.is_student:
            data.pop('correct_index', None)
        return data


class ExamSerializer(serializers.ModelSerializer):
    questions      = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.IntegerField(source='questions.count', read_only=True)
    course_title   = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model  = Exam
        fields = [
            'id', 'course', 'course_title', 'title',
            'max_retakes', 'created_at', 'questions', 'question_count',
        ]
        read_only_fields = ['id', 'created_at']


class ExamWriteSerializer(serializers.ModelSerializer):
    """Used when teacher creates/updates an exam with nested questions."""
    questions = QuestionSerializer(many=True)

    class Meta:
        model  = Exam
        fields = ['id', 'course', 'title', 'max_retakes', 'questions']
        read_only_fields = ['id']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        exam = Exam.objects.create(**validated_data)
        for idx, q in enumerate(questions_data):
            Question.objects.create(exam=exam, order=idx, **q)
        return exam

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            instance.questions.all().delete()
            for idx, q in enumerate(questions_data):
                Question.objects.create(exam=instance, order=idx, **q)
        return instance


class SubmitExamSerializer(serializers.Serializer):
    """Student submits answers. answers = { "0": 2, "1": "free text", ... }"""
    answers = serializers.DictField()


class ExamResultSerializer(serializers.ModelSerializer):
    student_name  = serializers.CharField(source='student.name',      read_only=True)
    exam_title    = serializers.CharField(source='exam.title',         read_only=True)
    course_id     = serializers.UUIDField(source='exam.course_id',     read_only=True)
    # Computed convenience fields so the frontend doesn't re-derive them
    correct       = serializers.SerializerMethodField()
    total_mcq     = serializers.SerializerMethodField()
    attempts_used = serializers.SerializerMethodField()
    can_retake    = serializers.SerializerMethodField()

    class Meta:
        model  = ExamResult
        fields = [
            'id', 'exam', 'exam_title', 'course_id',
            'student', 'student_name',
            'score', 'answers', 'open_grades',
            'submitted_at', 'attempt',
            'correct', 'total_mcq',
            'attempts_used', 'can_retake',
        ]
        read_only_fields = ['id', 'score', 'submitted_at', 'attempt']

    def get_correct(self, obj):
        """Number of correct MCQ answers in this attempt."""
        mcq_qs = obj.exam.questions.filter(type='mcq')
        correct = 0
        for q in mcq_qs:
            user_ans = obj.answers.get(str(q.order))
            if user_ans is not None and int(user_ans) == q.correct_index:
                correct += 1
        return correct

    def get_total_mcq(self, obj):
        return obj.exam.questions.filter(type='mcq').count()

    def get_attempts_used(self, obj):
        """Total attempts this student has made on this exam."""
        return ExamResult.objects.filter(
            exam=obj.exam, student=obj.student
        ).count()

    def get_can_retake(self, obj):
        """
        True if the student is allowed to retake.
        max_retakes=0 means unlimited.
        """
        max_retakes   = obj.exam.max_retakes
        attempts_used = self.get_attempts_used(obj)
        if max_retakes == 0:
            return True
        return attempts_used < max_retakes


class GradeOpenAnswerSerializer(serializers.Serializer):
    question_index = serializers.IntegerField()
    grade          = serializers.ChoiceField(
        choices=['Pass', 'Good', 'Excellent', 'Fail', ''],
        allow_blank=True,
    )
