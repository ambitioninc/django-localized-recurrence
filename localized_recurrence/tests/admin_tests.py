from django.test import TestCase

from localized_recurrence.admin import LocalizedRecurrenceAdmin


class LocalizedRecurrenceAdminTest(TestCase):
    """Verify that the admin can load.
    """
    def test_admin(self):
        LocalizedRecurrenceAdmin()
