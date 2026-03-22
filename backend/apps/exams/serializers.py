"""
apps/exams/serializers.py

IMPORTANT: exam.questions is a JSONField.
It is a plain Python LIST — not a queryset.
Never call .filter(), .get(), .exclude(), or .all() on it.
Always use list comprehensions or Python builtins (next(), filter(), etc.).
"""
from rest_framework import serializers
from .models import Exam, ExamAttempt, QuestionResponse


# ── Exam serializers ──────────────────────────────────────────────────────────

class ExamSerializer(serializers.ModelSerializer):
    """
    Full serializer — for teachers and exam builder.
    Questions include correct_index so the builder can display the right radio.
    """
    course_title   = serializers.CharField(source='course.title', read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model  = Exam
        fields = [
            'id', 'course', 'course_title', 'title', 'questions',
            'max_retakes', 'time_limit_minutes',
            'exam_weight', 'assignment_weight', 'passing_score',
            'question_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'course_title', 'question_count']

    def get_question_count(self, obj):
        # obj.questions is a list — use len(), not .count()
        return len(obj.questions or [])

    def validate(self, data):
        ew = data.get('exam_weight',       self.instance.exam_weight       if self.instance else 70)
        aw = data.get('assignment_weight', self.instance.assignment_weight if self.instance else 30)
        if ew + aw != 100:
            raise serializers.ValidationError(
                f'exam_weight ({ew}) + assignment_weight ({aw}) must equal 100.'
            )
        return data


class ExamForStudentSerializer(serializers.ModelSerializer):
    """
    Student-safe serializer — correct_index is stripped from every question.
    Sent before / during an exam attempt so students cannot see answers.
    """
    questions      = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()

    class Meta:
        model  = Exam
        fields = [
            'id', 'title', 'questions', 'question_count',
            'max_retakes', 'time_limit_minutes', 'passing_score',
        ]

    def get_questions(self, obj):
        """
        Return questions without correct_index.
        obj.questions is a list of dicts — iterate with a list comprehension.
        """
        safe = []
        for q in (obj.questions or []):
            safe.append({
                'type':    q.get('type'),
                'text':    q.get('text'),
                'options': q.get('options'),   # None for open questions
            })
        return safe

    def get_question_count(self, obj):
        return len(obj.questions or [])


# ── Helpers that work on the questions list ───────────────────────────────────

def _mcq_questions(questions_list):
    """Return all MCQ questions from the JSONField list."""
    return [q for q in (questions_list or []) if q.get('type') == 'mcq']


def _open_questions(questions_list):
    """Return all open questions from the JSONField list."""
    return [q for q in (questions_list or []) if q.get('type') != 'mcq']


def _correct_count(questions_list):
    """Count how many MCQ questions have a correct_index defined."""
    return sum(
        1 for q in _mcq_questions(questions_list)
        if q.get('correct_index') is not None
    )


# ── QuestionResponse serializers ──────────────────────────────────────────────

class QuestionResponseSerializer(serializers.ModelSerializer):
    """
    Student results view.
    - correct_index and is_correct are included (shown on the results page
      after submission).
    - teacher_feedback is hidden until the teacher has graded the response
      (graded_at is set).
    """
    teacher_feedback = serializers.SerializerMethodField()

    class Meta:
        model  = QuestionResponse
        fields = [
            'id', 'question_index', 'question_type', 'question_text',
            'options', 'selected_index', 'correct_index', 'text_answer',
            'max_points', 'points_earned', 'is_correct',
            'teacher_feedback', 'graded_at',
        ]

    def get_teacher_feedback(self, obj):
        # Only expose feedback once the teacher has saved a grade
        return obj.teacher_feedback if obj.graded_at else None


class QuestionResponseTeacherSerializer(serializers.ModelSerializer):
    """
    Teacher view — full data including student's text answers for manual grading.
    """
    student_name  = serializers.CharField(source='attempt.student.name',  read_only=True)
    student_email = serializers.CharField(source='attempt.student.email', read_only=True)
    attempt_id    = serializers.UUIDField(source='attempt.id',            read_only=True)
    exam_title    = serializers.CharField(source='attempt.exam.title',    read_only=True)

    class Meta:
        model  = QuestionResponse
        fields = [
            'id', 'attempt_id', 'student_name', 'student_email', 'exam_title',
            'question_index', 'question_type', 'question_text',
            'options', 'selected_index', 'correct_index', 'text_answer',
            'max_points', 'points_earned', 'is_correct',
            'teacher_feedback', 'graded_at',
        ]
        read_only_fields = [
            f for f in fields if f not in ('points_earned', 'teacher_feedback')
        ]


class GradeResponseSerializer(serializers.Serializer):
    """Used by QuestionResponseViewSet.grade to validate teacher input."""
    points_earned    = serializers.FloatField(min_value=0)
    teacher_feedback = serializers.CharField(allow_blank=True, default='')
    # max_points ceiling is checked in the view after fetching the object


# ── ExamAttempt serializers ───────────────────────────────────────────────────

class ExamAttemptSerializer(serializers.ModelSerializer):
    """
    Returned after /start/ and /submit/.
    Includes per-question responses for the student results page.
    """
    responses              = QuestionResponseSerializer(many=True, read_only=True)
    passed                 = serializers.BooleanField(read_only=True)
    open_questions_pending = serializers.BooleanField(read_only=True)
    student_name           = serializers.CharField(source='student.name', read_only=True)

    class Meta:
        model  = ExamAttempt
        fields = [
            'id', 'exam', 'student', 'student_name',
            'score', 'passed', 'open_questions_pending',
            'started_at', 'submitted_at', 'is_submitted',
            'time_limit_snapshot', 'auto_submitted',
            'responses',
        ]
        read_only_fields = fields


class ExamAttemptTeacherSerializer(serializers.ModelSerializer):
    """
    Teacher view — full question responses for reviewing / grading open answers.
    """
    responses              = QuestionResponseTeacherSerializer(many=True, read_only=True)
    student_name           = serializers.CharField(source='student.name',  read_only=True)
    student_email          = serializers.CharField(source='student.email', read_only=True)
    passed                 = serializers.BooleanField(read_only=True)
    open_questions_pending = serializers.BooleanField(read_only=True)

    class Meta:
        model  = ExamAttempt
        fields = [
            'id', 'exam', 'student', 'student_name', 'student_email',
            'score', 'passed', 'open_questions_pending',
            'started_at', 'submitted_at', 'is_submitted',
            'time_limit_snapshot', 'auto_submitted',
            'responses',
        ]
        read_only_fields = fields
