import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Exam new fields ────────────────────────────────────────────────────
        migrations.AddField(
            model_name='exam',
            name='time_limit_minutes',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exam',
            name='exam_weight',
            field=models.PositiveIntegerField(default=70),
        ),
        migrations.AddField(
            model_name='exam',
            name='assignment_weight',
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name='exam',
            name='passing_score',
            field=models.PositiveIntegerField(default=60),
        ),

        # ── ExamAttempt — change score to FloatField, add timing / status ──────
        migrations.AlterField(
            model_name='examattempt',
            name='score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='examattempt',
            name='submitted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='examattempt',
            name='time_limit_snapshot',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='examattempt',
            name='auto_submitted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='examattempt',
            name='is_submitted',
            field=models.BooleanField(default=False),
        ),

        # ── QuestionResponse (new table) ───────────────────────────────────────
        migrations.CreateModel(
            name='QuestionResponse',
            fields=[
                ('id',             models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('question_index', models.PositiveIntegerField()),
                ('question_type',  models.CharField(choices=[('mcq', 'Multiple Choice'), ('open', 'Open Answer')], max_length=10)),
                ('question_text',  models.TextField()),
                ('options',        models.JSONField(blank=True, null=True)),
                ('selected_index', models.IntegerField(blank=True, null=True)),
                ('text_answer',    models.TextField(blank=True)),
                ('correct_index',  models.IntegerField(blank=True, null=True)),
                ('max_points',     models.FloatField()),
                ('points_earned',  models.FloatField(blank=True, null=True)),
                ('is_correct',     models.BooleanField(blank=True, null=True)),
                ('teacher_feedback', models.TextField(blank=True)),
                ('graded_at',      models.DateTimeField(blank=True, null=True)),
                ('attempt', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='responses',
                    to='exams.examattempt',
                )),
            ],
            options={
                'db_table': 'question_responses',
                'ordering': ['question_index'],
                'unique_together': {('attempt', 'question_index')},
            },
        ),
    ]
