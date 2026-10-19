"""Offline configuration preflight: emits names/statuses, never credential values."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Check PayMongo and HTTPS configuration without calling the provider or database.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--strict', action='store_true', help='Fail if selected-mode credentials are missing or invalid.')
        parser.add_argument('--production', action='store_true', help='Also require live mode and production HTTPS settings.')

    def handle(self, *args, **options):
        mode = settings.PAYMONGO_MODE
        key = getattr(settings, 'PAYMONGO_SECRET_KEY_' + mode.upper(), '') or settings.PAYMONGO_SECRET_KEY
        signing_secret = getattr(settings, 'PAYMONGO_WEBHOOK_SECRET_' + mode.upper(), '')
        problems = []
        if mode not in ('test', 'live'):
            problems.append('PAYMONGO_MODE must be test or live.')
        if not key.startswith('sk_' + mode + '_'):
            problems.append('Selected-mode PayMongo secret key is missing or has the wrong mode prefix.')
        if not signing_secret:
            problems.append('PAYMONGO_WEBHOOK_SECRET_' + mode.upper() + ' is missing.')
        if options['production']:
            if mode != 'live':
                problems.append('Production activation requires PAYMONGO_MODE=live.')
            if settings.DEBUG:
                problems.append('Production requires DJANGO_DEBUG=False.')
            if not settings.CSRF_TRUSTED_ORIGINS or any(not origin.startswith('https://') for origin in settings.CSRF_TRUSTED_ORIGINS):
                problems.append('Production requires HTTPS DJANGO_CSRF_TRUSTED_ORIGINS.')
            if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS:
                problems.append('Production requires explicit DJANGO_ALLOWED_HOSTS.')
            if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
                problems.append('Production requires DJANGO_SECURE_SSL_REDIRECT=True.')
            if not getattr(settings, 'SESSION_COOKIE_SECURE', False) or not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                problems.append('Production requires secure session and CSRF cookies.')
        self.stdout.write('Mode: ' + mode)
        self.stdout.write('New QR checkouts: ' + ('enabled' if settings.PAYMONGO_ENABLED else 'disabled'))
        self.stdout.write('API credential: ' + ('configured for selected mode' if key.startswith('sk_' + mode + '_') else 'missing or wrong mode'))
        self.stdout.write('Webhook signing secret: ' + ('configured' if signing_secret else 'missing'))
        for problem in problems:
            self.stdout.write(self.style.WARNING(problem))
        if problems and (options['strict'] or options['production']):
            raise CommandError('Configuration check failed. Credential values were not displayed.')
        if not problems:
            self.stdout.write(self.style.SUCCESS('Offline configuration checks passed. Verify account activation, webhook delivery, and worker operation before enabling payments.'))
