import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Exam(models.Model):
    """
    One exam per course (OneToOne).

    Grading weights:
      exam_weight + assignment_weight must equal 100.
      Final grade = exam_best_score * (exam_weight/100)
                  + assignment_avg  * (assignment_weight/100)

    passing_score: minimum percentage to pass (default 60).
    time_limit_minutes: null means no time limit.
    max_retakes: 0 means unlimited retakes.
    """
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course              = models.OneToOneField(
        'courses.Course', on_delete=models.CASCADE, related_name='exam'
    )
    title               = models.CharField(max_length=200)
    questions           = models.JSONField(
        default=list,
        help_text='[{type, text, options?, correct_index?, points?}]'
    )
    max_retakes         = models.PositiveIntegerField(
        default=0, help_text='0 = unlimited'
    )
    time_limit_minutes  = models.PositiveIntegerField(
        null=True, blank=True, help_text='null = no limit'
    )
    exam_weight         = models.PositiveIntegerField(
        default=70, help_text='% of final course grade from this exam'
    )
    assignment_weight   = models.PositiveIntegerField(
        default=30, help_text='% of final course grade from assignments'
    )
    passing_score       = models.PositiveIntegerField(
        default=60, help_text='Minimum % score to pass'
    )
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exams'

    def __str__(self):
        return f'{self.course.title} — {self.title}'

    def clean(self):
        if (self.exam_weight + self.assignment_weight) != 100:
            raise ValidationError(
                f'exam_weight ({self.exam_weight}) + assignment_weight '
                f'({self.assignment_weight}) must equal 100.'
            )

    @property
    def points_per_question(self):
        """Equal weight per question. Override via question['points'] if needed."""
        n = len(self.questions)
        return round(100.0 / n, 4) if n else 0


class ExamAttempt(models.Model):
    """
    One attempt per student per exam start.
    Students may have multiple submitted attempts (subject to max_retakes).
    An in-progress attempt (is_submitted=False) is automatically resumed by /start/.
    """
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam                = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='attempts'
    )
    student             = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_attempts',
        limit_choices_to={'role': 'student'},
    )

    # Score — null until submitted; may remain < 100% while open Qs are ungraded.
    score               = models.FloatField(null=True, blank=True)

    # Timing
    started_at          = models.DateTimeField(auto_now_add=True)
    submitted_at        = models.DateTimeField(null=True, blank=True)
    # Snapshot of the exam's time_limit_minutes at the moment the attempt started.
    # Prevents teacher edits mid-attempt from affecting the running timer.
    time_limit_snapshot = models.PositiveIntegerField(null=True, blank=True)
    auto_submitted      = models.BooleanField(
        default=False, help_text='True when timer expired and backend auto-submitted'
    )
    is_submitted        = models.BooleanField(default=False)

    class Meta:
        db_table = 'exam_attempts'
        ordering = ['-started_at']

    def __str__(self):
        status = f'{self.score}%' if self.score is not None else 'in-progress'
        return f'{self.student.name} → {self.exam.title} [{status}]'

    @property
    def passed(self):
        if self.score is None:
            return None
        return self.score >= self.exam.passing_score

    @property
    def open_questions_pending(self):
        """True if there are open questions that still need teacher grading."""
        return self.responses.filter(
            question_type=QuestionResponse.TYPE_OPEN,
            points_earned__isnull=True
        ).exists()


class QuestionResponse(models.Model):
    """
    Stores the student's answer and the grade for a single question within one attempt.
    One row per question per attempt.

    MCQ:  auto-graded on submit  → is_correct + points_earned set immediately.
    Open: pending teacher grade  → points_earned is null until graded via /grade/.
    """
    TYPE_MCQ  = 'mcq'
    TYPE_OPEN = 'open'
    QUESTION_TYPES = [
        (TYPE_MCQ,  'Multiple Choice'),
        (TYPE_OPEN, 'Open Answer'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt        = models.ForeignKey(
        ExamAttempt, on_delete=models.CASCADE, related_name='responses'
    )
    question_index = models.PositiveIntegerField(help_text='0-based index into exam.questions')
    question_type  = models.CharField(max_length=10, choices=QUESTION_TYPES)

    # Question snapshot (so results are correct even if teacher edits exam later)
    question_text  = models.TextField()
    options        = models.JSONField(null=True, blank=True, help_text='List of option strings for MCQ')

    # Student answer
    selected_index = models.IntegerField(null=True, blank=True, help_text='MCQ: which option the student chose')
    text_answer    = models.TextField(blank=True, help_text='Open: free-text answer')

    # Correct answer snapshot (used for results page; hidden from students in serializer)
    correct_index  = models.IntegerField(null=True, blank=True)

    # Grading
    max_points     = models.FloatField(help_text='Points this question is worth')
    points_earned  = models.FloatField(null=True, blank=True, help_text='null = not yet graded (open Q)')
    is_correct     = models.BooleanField(null=True, blank=True, help_text='null for open / pending')

    # Teacher annotation (open questions)
    teacher_feedback = models.TextField(blank=True)
    graded_at        = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table        = 'question_responses'
        unique_together = ('attempt', 'question_index')
        ordering        = ['question_index']

    def __str__(self):
        return f'Q{self.question_index + 1} ({self.question_type}) — {self.attempt}'
