"""
Use this instead of `python manage.py runserver` when testing large video uploads.
waitress handles large request bodies without timeout issues on Windows.

Usage:
    python serve_dev.py

Install first:
    pip install waitress
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learnforge.settings')

from waitress import serve
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

print("LearnForge dev server running at http://localhost:8000")
print("Using waitress — safe for large video uploads")
print("Press Ctrl+C to stop\n")

serve(
    application,
    host='127.0.0.1',
    port=8000,
    threads=8,
    channel_timeout=600,    # 10 min — enough for a 2 GB upload on slow connection
    recv_bytes=0,           # no limit on request body size
)
