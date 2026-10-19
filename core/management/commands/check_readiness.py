from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Check local Gunicorn HTTP and database readiness."

    def handle(self, *args, **options):
        host = next((host.lstrip('.') for host in settings.ALLOWED_HOSTS if host != '*'), 'localhost')
        request = Request('http://127.0.0.1:8000/health/', headers={'Host': host})
        try:
            with urlopen(request, timeout=5) as response:
                if response.status != 200 or response.read() != b'{"status": "ok"}':
                    raise CommandError('Application is not ready')
        except (URLError, TimeoutError, OSError):
            raise CommandError('Application is not ready') from None
