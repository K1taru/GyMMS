import ast
from io import StringIO
from pathlib import Path
import re

from django.conf import settings
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, override_settings


class ConfigurationTests(SimpleTestCase):
    def test_example_has_unique_recognized_names_and_no_legacy_aliases(self):
        example = Path(settings.BASE_DIR, '.env.example').read_text()
        names = [line.split('=', 1)[0].strip() for line in example.splitlines()
                 if '=' in line and not line.lstrip().startswith('#')]
        self.assertEqual(len(names), len(set(names)))
        self.assertFalse({'SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS'} & set(names))
        source = Path(settings.BASE_DIR, 'config/settings.py').read_text()
        reads = set()
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            function = node.func
            is_env = isinstance(function, ast.Name) and function.id == 'env'
            is_env_method = (isinstance(function, ast.Attribute)
                             and isinstance(function.value, ast.Name)
                             and function.value.id == 'env')
            if is_env or is_env_method:
                reads.add(ast.literal_eval(node.args[0]))
        # Keep every runtime option discoverable and reject stale aliases.
        self.assertEqual(set(names), reads)
        secrets = {'DJANGO_SECRET_KEY', 'PAYMONGO_SECRET_KEY', 'PAYMONGO_SECRET_KEY_TEST',
                   'PAYMONGO_SECRET_KEY_LIVE', 'PAYMONGO_WEBHOOK_SECRET_TEST', 'PAYMONGO_WEBHOOK_SECRET_LIVE'}
        values = dict(line.split('=', 1) for line in example.splitlines()
                      if '=' in line and not line.lstrip().startswith('#'))
        self.assertTrue(all(not values[name] for name in secrets))

    def test_compose_maps_database_names_to_postgres_initialization_variables(self):
        compose = Path(settings.BASE_DIR, 'docker-compose.yml').read_text()
        mappings = re.findall(
            r'^\s+(POSTGRES_[A-Z_]+):\s*\$\{([A-Z_]+)\}\s*$', compose, re.MULTILINE
        )
        self.assertEqual(len(mappings), 3)
        self.assertEqual(dict(mappings), {
            'POSTGRES_DB': 'DB_NAME',
            'POSTGRES_USER': 'DB_USER',
            'POSTGRES_PASSWORD': 'DB_PASSWORD',
        })

    @override_settings(PAYMONGO_MODE='test', PAYMONGO_ENABLED=False,
                       PAYMONGO_SECRET_KEY='', PAYMONGO_SECRET_KEY_TEST='', PAYMONGO_WEBHOOK_SECRET_TEST='')
    def test_strict_preflight_rejects_missing_credentials_without_network_or_database(self):
        output = StringIO()
        with self.assertRaises(CommandError):
            call_command('check_paymongo', '--strict', stdout=output)
        self.assertIn('missing', output.getvalue())

    @override_settings(PAYMONGO_MODE='test', PAYMONGO_ENABLED=False,
                       PAYMONGO_SECRET_KEY='sk_live_wrong_mode', PAYMONGO_SECRET_KEY_TEST='sk_test_do_not_print',
                       PAYMONGO_WEBHOOK_SECRET_TEST='do_not_print_signing_secret')
    def test_preflight_mode_specific_key_takes_precedence_and_secrets_are_never_printed(self):
        output = StringIO()
        call_command('check_paymongo', '--strict', stdout=output)
        self.assertIn('Offline configuration checks passed', output.getvalue())
        self.assertNotIn('do_not_print', output.getvalue())
        self.assertNotIn('sk_live_wrong_mode', output.getvalue())

    @override_settings(DEBUG=True, PAYMONGO_MODE='test', PAYMONGO_SECRET_KEY='sk_test_fixture',
                       PAYMONGO_SECRET_KEY_TEST='', PAYMONGO_WEBHOOK_SECRET_TEST='fixture')
    def test_production_preflight_rejects_test_mode_and_development_security(self):
        with self.assertRaises(CommandError):
            call_command('check_paymongo', '--production', stdout=StringIO())
