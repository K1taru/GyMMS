import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, OperationalError, InterfaceError

class Command(BaseCommand):
    """Django command to wait for database availability"""

    def add_arguments(self, parser):
        parser.add_argument('--attempts', type=int, default=30)
        parser.add_argument('--interval', type=float, default=2)

    def handle(self, *args, **options):
        attempts, interval = options['attempts'], options['interval']
        if attempts < 1 or interval < 0:
            raise CommandError('Attempts must be positive and interval nonnegative')
        for attempt in range(attempts):
            try:
                with connections['default'].cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
            except (OperationalError, InterfaceError):
                connections['default'].close()
                if attempt + 1 == attempts:
                    raise CommandError('Database unavailable after bounded retries') from None
                self.stdout.write('Database unavailable; retrying...')
                time.sleep(interval)
            else:
                self.stdout.write(self.style.SUCCESS('Database available'))
                return
