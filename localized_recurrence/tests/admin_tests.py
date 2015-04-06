from django.test import TestCase

from localized_recurrence.admin import LocalizedRecurrenceAdmin


class LocalizedRecurrenceAdminTests(TestCase):
    def test_admin():
        LocalizedRecurrenceAdmin()
