from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from localized_recurrence.models import LocalizedRecurrence


class LocalizedRecurrenceAdminTest(TestCase):
    """Verify that the admin can load.
    """
    def test_admin(self):
        site = AdminSite()
        ModelAdmin(LocalizedRecurrence, site)
