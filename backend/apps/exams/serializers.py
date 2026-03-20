from rest_framework import serializers
from .models import Exam, Question, ExamResult


class QuestionSerializer(serializers.ModelSerializer):
    # image_url is a read-only absolute URL sent back to the client.
    # The writable `image` field (FileField) is write_only so the URL
    # isn't double-serialized alongside the upload field.
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Question
        fields = ['id', 'type', 'text', 'image', 'image_url',
                  'options', 'correct_index', 'order']
        extra_kwargs = {
            'image': {'write_only': True, 'required': False},
        }

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

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
    """Used when teacher creates/updates an exam with nested questions (text/options only).
    Images are uploaded separately via PATCH /exams/<exam_pk>/questions/<pk>/."""
    questions = QuestionSerializer(many=True)

    class Meta:
        model  = Exam
        fields = ['id', 'course', 'title', 'max_retakes', 'questions']
        read_only_fields = ['id']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        exam = Exam.objects.create(**validated_data)
        for idx, q in enumerate(questions_data):
            q.pop('image', None)   # images come via separate PATCH
            Question.objects.create(exam=exam, order=idx, **q)
        return exam

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            # Preserve existing images when rebuilding the question list:
            # match by order so an image uploaded before a save is kept.
            old_images = {q.order: q.image for q in instance.questions.all()}
            instance.questions.all().delete()
            for idx, q in enumerate(questions_data):
                q.pop('image', None)
                new_q = Question.objects.create(exam=instance, order=idx, **q)
                if old_images.get(idx):
                    new_q.image = old_images[idx]
                    new_q.save(update_fields=['image'])
        return instance


class SubmitExamSerializer(serializers.Serializer):
    """Student submits answers. answers = { "0": 2, "1": "free text", ... }"""
    answers = serializers.DictField()


class ExamResultSerializer(serializers.ModelSerializer):
    student_name  = serializers.CharField(source='student.name',      read_only=True)
    exam_title    = serializers.CharField(source='exam.title',         read_only=True)
    course_id     = serializers.UUIDField(source='exam.course_id',     read_only=True)
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
        return ExamResult.objects.filter(
            exam=obj.exam, student=obj.student
        ).count()

    def get_can_retake(self, obj):
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