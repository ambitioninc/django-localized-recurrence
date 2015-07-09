from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from localized_recurrence.admin import LocalizedRecurrenceAdmin
from localized_recurrence.models import LocalizedRecurrence


class LocalizedRecurrenceAdminTest(TestCase):
    """Verify that the admin can load.
    """
    def setUp(self):
        super(LocalizedRecurrenceAdminTest, self).setUp()
        self.site = AdminSite()

    def test_model_admin_load(self):
        lr_admin = LocalizedRecurrenceAdmin(LocalizedRecurrence, self.site)
        self.assertEqual(
            lr_admin.list_display,
            [
                'id',
                'interval',
                'timezone',
                'offset',
                'previous_scheduled',
                'next_scheduled'
            ]
        )
