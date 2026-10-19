import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(SECURE_SSL_REDIRECT=False)
class OwnerProvisioningTests(TestCase):
    def test_createsuperuser_provisions_owner_who_can_log_in_and_access_owner_pages(self):
        password = 'owner-test-password-only'
        with patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': password}):
            call_command('createsuperuser', username='new-owner',
                         email='owner@example.test', interactive=False, stdout=StringIO())

        owner = get_user_model().objects.get(username='new-owner')
        self.assertEqual(owner.role, 'Owner')
        self.assertTrue(owner.is_active)
        self.assertTrue(owner.is_staff)
        self.assertTrue(owner.is_superuser)
        self.assertNotEqual(owner.password, password)
        self.assertEqual(authenticate(username=owner.username, password=password), owner)
        self.assertTrue(self.client.login(username=owner.username, password=password))
        self.assertEqual(self.client.get(reverse('users:staff_management')).status_code, 200)

    def test_ordinary_user_defaults_to_staff_and_cannot_access_owner_pages(self):
        staff = get_user_model().objects.create_user(username='new-staff', password='staff-test-only')
        self.assertEqual(staff.role, 'Staff')
        self.assertFalse(staff.is_staff)
        self.assertFalse(staff.is_superuser)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('users:staff_management')).status_code, 403)

    def test_superuser_rejects_conflicting_role_or_permissions(self):
        for extra_fields in ({'role': 'Staff'}, {'is_active': False},
                             {'is_staff': False}, {'is_superuser': False}):
            with self.subTest(extra_fields=extra_fields), self.assertRaises(ValueError):
                get_user_model().objects.create_superuser(username='invalid-owner', **extra_fields)
