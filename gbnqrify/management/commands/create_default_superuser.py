from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Create a default superuser if no users exist'

    def handle(self, *args, **options):
        User = get_user_model()

        # Check if any users exist
        if User.objects.exists():
            self.stdout.write(
                self.style.WARNING('Users already exist. Skipping superuser creation.')
            )
            return

        # Get credentials from environment variables or use defaults
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gbnqr.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser "{username}" with password "{password}"'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
