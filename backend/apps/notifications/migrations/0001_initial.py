import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(
                    choices=[
                        ('qa_answer',    'Q&A Answer'),
                        ('exam_graded',  'Exam Graded'),
                        ('cert_issued',  'Certificate Issued'),
                        ('announcement', 'Announcement'),
                    ],
                    max_length=20,
                )),
                ('title',    models.CharField(max_length=200)),
                ('body',     models.TextField(blank=True)),
                ('link',     models.CharField(blank=True, max_length=500)),
                ('is_read',  models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'notifications',
                'ordering': ['-created_at'],
            },
        ),
    ]
