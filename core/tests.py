import signal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings


@override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=True)
class ReadinessTests(TestCase):
    def test_health_works_over_http_in_production(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.client.get('/').status_code, 301)

    def test_database_failure_is_generic(self):
        with patch('core.health.connection.cursor', side_effect=OperationalError('private details')):
            response = self.client.get('/health/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})


class DatabaseWaitTests(SimpleTestCase):
    def test_wait_retries_real_connection_and_stops(self):
        with patch('core.management.commands.wait_for_db.connections') as connections:
            database = connections.__getitem__.return_value
            database.cursor.side_effect = OperationalError('private credentials')
            with self.assertRaisesMessage(CommandError, 'Database unavailable after bounded retries'):
                call_command('wait_for_db', attempts=2, interval=0, stdout=StringIO())
            self.assertEqual(database.cursor.call_count, 2)

    def test_wait_recovers_and_executes_query(self):
        with patch('core.management.commands.wait_for_db.connections') as connections:
            database = connections.__getitem__.return_value
            cursor = database.cursor.return_value.__enter__.return_value
            call_command('wait_for_db', attempts=1, stdout=StringIO())
            cursor.execute.assert_called_once_with('SELECT 1')


@override_settings(ALLOWED_HOSTS=['gym.example.test'])
class ReadinessCommandTests(SimpleTestCase):
    def test_probe_uses_configured_host(self):
        with patch('core.management.commands.check_readiness.urlopen') as open_url:
            response = open_url.return_value.__enter__.return_value
            response.status = 200
            response.read.return_value = b'{"status": "ok"}'
            call_command('check_readiness')
            request = open_url.call_args.args[0]
            self.assertEqual(request.get_header('Host'), 'gym.example.test')
            self.assertEqual(request.full_url, 'http://127.0.0.1:8000/health/')

    def test_probe_reports_generic_failure(self):
        with patch('core.management.commands.check_readiness.urlopen', side_effect=OSError('private details')):
            with self.assertRaisesMessage(CommandError, 'Application is not ready'):
                call_command('check_readiness')


class WorkerShutdownTests(SimpleTestCase):
    def test_sigterm_finishes_current_batch_and_exits(self):
        old_handler = signal.getsignal(signal.SIGTERM)

        def tick(**kwargs):
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
            self.assertTrue(kwargs['stop_requested']())

        with patch('payments.management.commands.payment_worker.worker_tick', side_effect=tick) as worker:
            call_command('payment_worker', loop=True)
            worker.assert_called_once()
        self.assertEqual(signal.getsignal(signal.SIGTERM), old_handler)
