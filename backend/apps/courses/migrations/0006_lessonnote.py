import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_lessonattachment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LessonNote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('body', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lesson', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notes',
                    to='courses.lesson',
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='lesson_notes',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'lesson_notes',
                'unique_together': {('student', 'lesson')},
            },
        ),
    ]
