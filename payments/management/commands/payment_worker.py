import signal
from threading import Event
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
        stopping = Event()

        def stop(signum, frame):
            stopping.set()

        previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
        try:
            while not stopping.is_set():
                close_old_connections()
                worker_tick(stop_requested=stopping.is_set)
                if options['once']:
                    return
                stopping.wait(2)
        finally:
            close_old_connections()
            for sig, handler in previous.items():
                signal.signal(sig, handler)
