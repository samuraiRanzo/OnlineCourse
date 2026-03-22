import uuid
import apps.assignments.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0006_lessonnote'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id',          models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title',       models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('due_date',    models.DateTimeField(blank=True, null=True)),
                ('max_score',   models.PositiveIntegerField(default=100)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('lesson', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to='courses.lesson',
                )),
            ],
            options={
                'db_table': 'assignments',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id',          models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file',        models.FileField(blank=True, null=True, upload_to=apps.assignments.models.submission_upload_path)),
                ('text_answer', models.TextField(blank=True)),
                ('score',       models.PositiveIntegerField(blank=True, null=True)),
                ('feedback',    models.TextField(blank=True)),
                ('graded_at',   models.DateTimeField(blank=True, null=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at',   models.DateTimeField(auto_now=True)),
                ('assignment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='submissions',
                    to='assignments.assignment',
                )),
                ('student', models.ForeignKey(
                    limit_choices_to={'role': 'student'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='submissions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'submissions',
                'ordering': ['-updated_at'],
                'unique_together': {('student', 'assignment')},
            },
        ),
    ]
