import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from payments.services.qrph import worker_tick


class Command(BaseCommand):
    help = 'Generate QRPh checkouts, consume durable webhooks, and reconcile provider state.'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--once', action='store_true', help='Run one bounded batch and exit.')
        group.add_argument('--loop', action='store_true', help='Continuously process jobs (default).')

    def handle(self, *args, **options):
        while True:
            close_old_connections()
            worker_tick()
            if options['once']:
                return
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                return
