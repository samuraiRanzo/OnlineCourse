"""
Usage:
    python manage.py create_teacher
    python manage.py create_teacher --email teacher@school.com --name "Alex Teacher" --password secret123
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create the first teacher (admin) account for LearnForge'

    def add_arguments(self, parser):
        parser.add_argument('--email',    type=str, default='')
        parser.add_argument('--name',     type=str, default='')
        parser.add_argument('--password', type=str, default='')

    def handle(self, *args, **options):
        email    = options['email']    or self._prompt('Email address: ')
        name     = options['name']     or self._prompt('Full name: ')
        password = options['password'] or self._prompt('Password (min 6 chars): ', secret=True)

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(
                f'A user with email "{email}" already exists. Skipping.'
            ))
            return

        if len(password) < 6:
            self.stderr.write(self.style.ERROR('Password must be at least 6 characters.'))
            return

        user = User.objects.create_user(
            email=email,
            name=name,
            password=password,
            role='admin',
            is_staff=True,
            is_superuser=True,
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Teacher account created successfully!\n'
            f'   Name  : {user.name}\n'
            f'   Email : {user.email}\n'
            f'   Role  : Admin / Teacher\n\n'
            f'You can now log in at http://localhost:5173/login\n'
        ))

    def _prompt(self, text, secret=False):
        if secret:
            import getpass
            return getpass.getpass(text)
        return input(text).strip()
