from datetime import datetime, timedelta

import django
from django.test import TestCase
from django_dynamic_fixture import G
from django.utils import timezone
import pytz

from ..models import LocalizedRecurrence, LocalizedRecurrenceQuerySet
from ..models import _replace_with_offset, _update_schedule, _prepare_datetime_field_value


class LocalizedRecurrenceUpdateTest(TestCase):
    """
    Tests calling 'update' on a localized recurrence.
    """
    def test_update_creation(self):
        lr = LocalizedRecurrence()
        lr.update()
        self.assertIsNotNone(lr.id)

    def test_update_timezone(self):
        lr = G(LocalizedRecurrence)
        lr.update(timezone='US/Eastern')
        lr = LocalizedRecurrence.objects.get(id=lr.id)
        self.assertEqual(lr.timezone, pytz.timezone('US/Eastern'))

    def test_update_offset(self):
        lr = G(LocalizedRecurrence)
        lr.update(offset=timedelta(seconds=1))
        lr = LocalizedRecurrence.objects.get(id=lr.id)
        self.assertEqual(lr.offset, timedelta(seconds=1))


class LocalizedRecurrenceQuerySetTest(TestCase):
    """Simple test to ensure the custom query set is being used.
    """
    def test_isinstance(self):
        G(LocalizedRecurrence)
        recurrences = LocalizedRecurrence.objects.all()
        self.assertIsInstance(recurrences, LocalizedRecurrenceQuerySet)


class LocalizedRecurrenceQuerySetUpdateScheduleTest(TestCase):
    """Test that updates to recurrences are reflected in the DB.
    """
    def setUp(self):
        G(LocalizedRecurrence, interval='DAY', offset=timedelta(hours=12), timezone=pytz.timezone('US/Eastern'))
        G(LocalizedRecurrence, interval='MONTH', offset=timedelta(hours=15), timezone=pytz.timezone('US/Eastern'))

    def test_update_from_1970(self):
        """Start with next_scheduled of 1970, after update should be new.
        """
        time = datetime(year=2013, month=5, day=20, hour=12, minute=3)
        LocalizedRecurrence.objects.filter(interval='DAY').update_schedule(time=time)
        lr_day = LocalizedRecurrence.objects.filter(interval='DAY').first()
        self.assertGreater(lr_day.next_scheduled, time)


class LocalizedRecurrenceManagerUpdateScheduleTest(TestCase):
    def setUp(self):
        G(LocalizedRecurrence, interval='DAY', offset=timedelta(hours=12), timezone=pytz.timezone('US/Eastern'))
        G(LocalizedRecurrence, interval='MONTH', offset=timedelta(hours=15), timezone=pytz.timezone('US/Eastern'))

    def test_update_all(self):
        """Calls to the model manager to update should be passed through.
        """
        time = datetime(year=2013, month=5, day=20, hour=15, minute=3)
        LocalizedRecurrence.objects.update_schedule(time=time)
        self.assertTrue(all(r.next_scheduled > time for r in LocalizedRecurrence.objects.all()))


class LocalizedRecurrenceTest(TestCase):
    """Test the creation and querying of LocalizedRecurrence records.
    """
    def setUp(self):
        G(LocalizedRecurrence, interval='DAY', offset=timedelta(hours=12), timezone=pytz.timezone('US/Eastern'))

    def test_timedelta_returned(self):
        """Test that the Duration field is correctly returning timedeltas.
        """
        lr = LocalizedRecurrence.objects.first()
        self.assertTrue(isinstance(lr.offset, timedelta))

    def test_string_representation(self):
        lr = LocalizedRecurrence.objects.first()
        self.assertEqual(
            str(lr),
            'ID: {0}, Interval: {1}, Next Scheduled: {2}'.format(lr.id, lr.interval, lr.next_scheduled),
        )


class LocalizedRecurrenceUpdateScheduleTest(TestCase):
    def setUp(self):
        self.lr_day = G(LocalizedRecurrence,
                        interval='DAY', offset=timedelta(hours=12), timezone=pytz.timezone('US/Eastern'))

    def test_update_passes_through(self):
        time = datetime(year=2013, month=5, day=20, hour=15, minute=3)
        self.lr_day.update_schedule(time)
        self.assertGreater(self.lr_day.next_scheduled, time)


class LocalizedRecurrenceUtcOfNextScheduleTest(TestCase):
    def setUp(self):
        self.lr_day = G(
            LocalizedRecurrence,
            interval='DAY', offset=timedelta(hours=12),
            timezone=pytz.timezone('US/Eastern'))
        self.lr_week = G(
            LocalizedRecurrence,
            interval='WEEK', offset=timedelta(days=3, hours=17, minutes=30),
            timezone=pytz.timezone('US/Central'))
        self.lr_month = G(
            LocalizedRecurrence,
            interval='MONTH', offset=timedelta(days=21, hours=19, minutes=15, seconds=10),
            timezone=pytz.timezone('US/Central'))
        self.lr_quarter = G(
            LocalizedRecurrence,
            interval='QUARTER', offset=timedelta(days=68, hours=16, minutes=30),
            timezone=pytz.timezone('Asia/Hong_Kong'))
        self.lr_year = G(
            LocalizedRecurrence,
            interval='YEAR', offset=timedelta(days=31, hours=16, minutes=30),
            timezone=pytz.timezone('Asia/Hong_Kong'))

    def test_basic_works(self):
        """
        Test a simple case of utc_of_next_schedule.

        - The given recurrence is scheduled daily for Eastern Time at noon.
        - The given current date in UTC is 2013/1/15::17:05:22
        - We then expect the next schedule in UTC to be 2013/1/16::17:0:0
        """
        current_time = datetime(2013, 1, 15, 17, 5, 22)
        expected_next_schedule = datetime(2013, 1, 16, 17)
        schedule_out = self.lr_day.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_dst_cross_monthly(self):
        """The case when a monthly recurrence goes past daylight savings time"""
        self.lr_month.offset = timedelta(hours=0)
        self.lr_month.previous_scheduled = datetime(2015, 2, 1, 6)
        scheduled_out = self.lr_month.utc_of_next_schedule(datetime(2015, 3, 31))
        self.assertEqual(scheduled_out, datetime(2015, 4, 1, 5))

    def test_before_midnight(self):
        """The case when the scheduled and current time cross midnight.

        - The given recurrence is scheduled daily for Eastern Time at 11:59PM.
        - The given current date in UTC is 2013/1/15::05:05:22 -> 12:05AM EST
        - We then expect the next schedule in UTC to be 2013/1/16::05:0:0
        """
        self.lr_day.offset = timedelta(hours=23, minutes=59)
        self.lr_day.save()
        current_time = datetime(2013, 1, 15, 5, 5, 22)
        expected_next_schedule = datetime(2013, 1, 16, 4, 59)
        schedule_out = self.lr_day.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_after_midnight(self):
        """
        The case when the scheduled and current time are after midnight.

        - The given recurrence is scheduled daily for Eastern Time at 12:01 AM.
        - The given current date in UTC is 2013/1/15::05:05:22 -> 12:05AM EST
        - We then expect the next schedule in UTC to be 2013/1/16::05:01:0
        """
        self.lr_day.offset = timedelta(minutes=1)
        self.lr_day.save()
        current_time = datetime(2013, 1, 15, 5, 5, 22)
        expected_next_schedule = datetime(2013, 1, 16, 5, 1)
        schedule_out = self.lr_day.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_week_update_full_week(self):
        """
        Weekly Recurrences should be able to add a full week.

        - Thursday August 8th at 10:34 PM UTC is 5:34 PM CDT.
        - Scheduled for weekly, Thursday at 5:30
        - Expect next schedule to be Thursday August 15th at 10:30 PM UTC
        """
        current_time = datetime(2013, 8, 8, 22, 34)
        expected_next_schedule = datetime(2013, 8, 15, 22, 30)
        schedule_out = self.lr_week.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_weekly_update_current_week(self):
        """
        Weekly Recurrences should be able to work in the current week.

        - Tuesday August 6th at 10:34 PM UTC is 5:34 PM CDT.
        - Scheduled for weekly, Thursday at 5:30
        - Expect next schedule to be Thursday August 8th at 10:30 PM UTC
        """
        current_time = datetime(2013, 8, 6, 22, 34)
        expected_next_schedule = datetime(2013, 8, 8, 22, 30)
        schedule_out = self.lr_week.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_month_update_full_month(self):
        """
        Monthly Recurrences should work as expected moving forward a full month.

        - Friday August 23rd at 12:34 AM UTC is Thursday August 22nd at 7:34 PM CDT.
        - Scheduled for Monthly, on the 21st day at 7:15.10 PM
        - Expect next schedule to be September 23 at 12:15.10 AM UTC
        """
        current_time = datetime(2013, 8, 23, 0, 34, 55)
        expected_next_schedule = datetime(2013, 9, 23, 0, 15, 10)
        schedule_out = self.lr_month.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_month_update_current_month(self):
        """
        Monthly Recurrences should work as expected moving forward in the
        current month.

        - Friday August 16th at 12:34 AM UTC is Thursday August 15th at 7:34 PM CDT.
        - Scheduled for Monthly, on the 21st day at 7:15.10 PM
        - Expect next schedule to be August 23 at 12:15.10 AM UTC

        """
        current_time = datetime(2013, 8, 16, 0, 34, 55)
        expected_next_schedule = datetime(2013, 8, 23, 0, 15, 10)
        schedule_out = self.lr_month.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_month_year_end_update(self):
        """
        Monthly Recurrences should transition over years correctly

        - Monday December 23 at 2:34 AM UTC is Sunday August 22nd at 9:34 PM CDT.
        - Scheduled for Monthly, on the 21st day at 7:15.10 PM CDT
        - Expect next schedule to be January 23 at 1:15.10 AM UCT
        """
        current_time = datetime(2013, 12, 23, 2, 34, 55)
        expected_next_schedule = datetime(2014, 1, 23, 1, 15, 10)
        schedule_out = self.lr_month.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_quarterly_full_quarter(self):
        """
        Quarterly Recurrences should be able to update a full quarter.

        - June 23rd at 12:34 AM UTC is June 22nd at 10:34 PM HKT.
        - Scheduled for Quarterly, on the 68th day at 4:30 PM HKT
        - Expect next schedule to be September 7th at 8:30 AM UTC
        """
        current_time = datetime(2013, 6, 23, 0, 34, 55)
        expected_next_schedule = datetime(2013, 9, 7, 8, 30)
        schedule_out = self.lr_quarter.utc_of_next_schedule(current_time)
        self.lr_quarter = G(
            LocalizedRecurrence,
            interval='QUARTER',
            offset=timedelta(days=68, hours=16, minutes=30),
            timezone=pytz.timezone('Asia/Hong_Kong')
        )
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_quarterly_current_quarter(self):
        """
        Quarterly Recurrences should be able to update in the current quarter.

        - April 23rd at 12:34 AM UTC is April 22nd at 10:34 PM HKT.
        - Scheduled for Quarterly, on the 68th day at 4:30 PM HKT
        - Expect next schedule to be June 8th at 8:30 AM UTC
        """
        current_time = datetime(2013, 4, 23, 0, 34, 55)
        expected_next_schedule = datetime(2013, 6, 8, 8, 30)
        schedule_out = self.lr_quarter.utc_of_next_schedule(current_time)

        self.lr_quarter = G(
            LocalizedRecurrence,
            interval='QUARTER',
            offset=timedelta(days=68, hours=16, minutes=30),
            timezone=pytz.timezone('Asia/Hong_Kong')
        )

        self.assertEqual(schedule_out, expected_next_schedule)

    def test_quarterly_end_year(self):
        """
        Quarterly Recurrences should be able to update through year end.

        - December 23rd at 12:34 AM UTC is April 22nd at 10:34 PM HKT.
        - Scheduled for Quarterly, on the 68th day at 4:30 PM HKT
        - Expect next schedule to be March 10th at 8:30 AM UTC
        """
        current_time = datetime(2013, 12, 23, 0, 34, 55)
        expected_next_schedule = datetime(2014, 3, 10, 8, 30)
        schedule_out = self.lr_quarter.utc_of_next_schedule(current_time)
        self.lr_quarter = G(
            LocalizedRecurrence,
            interval='QUARTER',
            offset=timedelta(days=68, hours=16, minutes=30),
            timezone=pytz.timezone('Asia/Hong_Kong')
        )
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_yearly(self):
        """
        Yearly Recurrences should work as expected.

        - June 23rd at 12:34 AM UTC is June 22nd at 10:34 PM HKT.
        - Scheduled for Yearly, on the 31st day at 4:30 PM HKT
        - Expect next schedule to be February 1st at 8:30 AM UTC
        """
        current_time = datetime(2013, 6, 23, 0, 34, 55)
        expected_next_schedule = datetime(2014, 2, 1, 8, 30)
        schedule_out = self.lr_year.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_into_dst_boundary(self):
        """
        Recurrences happen at the correct local time after going into DST.

        Going into daylight savings time should mean the UTC time is
        an hour less on the next recurrence.

        - 2013 US DST began: Sunday March 10th.
        - Weekly recurence, every Thursday at Noon EST.
        """
        self.lr_week.offset = timedelta(days=3, hours=12)
        self.lr_week.save()
        current_time = datetime(2013, 3, 7, 18)
        expected_next_schedule = datetime(2013, 3, 14, 17)
        schedule_out = self.lr_week.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_out_of_dst_boundary(self):
        """
        Recurrences at the correct local time after going out of UTC.

        Going into daylight savings time should mean the UTC time is
        an hour greater on the next recurrence.

        - 2013 US DST ended: Sunday November 3rd.
        - Weekly recurence, every Thursday at Noon EST.
        """
        self.lr_week.offset = timedelta(days=3, hours=12)
        self.lr_week.save()
        current_time = datetime(2013, 10, 31, 17)
        expected_next_schedule = datetime(2013, 11, 7, 18)
        schedule_out = self.lr_week.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)

    def test_utc_plus(self):
        """
        Test a timezone that is UTC + 2.

        - Europe/Berlin DST is UTC + 2
        """
        self.lr_day.timezone = pytz.timezone('Europe/Berlin')
        self.lr_day.save()
        current_time = datetime(2013, 5, 5, 10, 10)
        expected_next_schedule = datetime(2013, 5, 6, 10)
        schedule_out = self.lr_day.utc_of_next_schedule(current_time)
        self.assertEqual(schedule_out, expected_next_schedule)


class UpdateScheduleTest(TestCase):
    def setUp(self):
        self.lr_week = G(
            LocalizedRecurrence,
            interval='WEEK', offset=timedelta(hours=12),
            timezone=pytz.timezone('US/Eastern'))
        self.lr_day = G(
            LocalizedRecurrence,
            interval='DAY',
            offset=timedelta(hours=12),
            timezone=pytz.timezone('US/Eastern'))

    def test_updates_localized_recurrences(self):
        time = datetime(year=2013, month=5, day=20, hour=12, minute=3)
        _update_schedule([self.lr_week], time)
        self.assertGreater(self.lr_week.next_scheduled, time)
        self.assertEqual(self.lr_week.previous_scheduled, time)


class ReplaceWithOffsetTest(TestCase):
    def test_day(self):
        """
        _replace_with_offset works as expected with a 'DAY' interval.
        """
        dt_in = datetime(2013, 1, 20, 12, 45, 48)
        td_in = timedelta(hours=3, minutes=3, seconds=3)
        interval_in = 'DAY'
        dt_expected = datetime(2013, 1, 20, 3, 3, 3)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_out, dt_expected)

    def test_week(self):
        """
        _replace_with_offset works as expected with a 'WEEK' interval.
        """
        dt_in = datetime(2013, 1, 20, 12, 45, 48)
        td_in = timedelta(days=4, hours=3, minutes=3, seconds=3)
        interval_in = 'WEEK'
        dt_expected = datetime(2013, 1, 18, 3, 3, 3)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_out, dt_expected)

    def test_week_on_month_boundary(self):
        """
        _replace_with_offset using interval 'WEEK' should roll over months
        correctly.
        """
        dt_in = datetime(2013, 7, 30, 12, 45, 48)
        td_in = timedelta(days=4, hours=3, minutes=3, seconds=3)
        interval_in = 'WEEK'
        dt_expected = datetime(2013, 8, 2, 3, 3, 3)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_out, dt_expected)

    def test_month(self):
        """
        _replace_with_offset works as expected with a 'MONTH' interval.
        """
        dt_in = datetime(2013, 1, 20, 12, 45, 48)
        td_in = timedelta(days=15, hours=3, minutes=3, seconds=3)
        interval_in = 'MONTH'
        dt_expected = datetime(2013, 1, 16, 3, 3, 3)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_out, dt_expected)

    def test_last_day_of_month(self):
        """
        Check dates for a full year where the utc time is the first and the time zone is the previous day
        """
        time_delta = timedelta(days=30, hours=23, minutes=3, seconds=3)
        dt_start = datetime(2013, 2, 20, 23, 45, 48)
        interval_name = 'MONTH'
        timezone_name = 'US/Central'
        recurrence = LocalizedRecurrence.objects.create(
            interval=interval_name,
            offset=time_delta,
            timezone=timezone_name,
            next_scheduled=dt_start,
        )

        # Check a full year of dates. The first next recurrence should be the month after it starts because
        # The start time is weird because it should be set correctly to begin with. Setting it to 2-20 should not
        # be happening. The app should initially set it to the correct first fire date
        self.assertEqual(recurrence.next_scheduled, datetime(2013, 2, 20, 23, 45, 48))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 4, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 5, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 6, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 7, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 8, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 9, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 10, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 11, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2013, 12, 1, 5, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2014, 1, 1, 5, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2014, 2, 1, 5, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2014, 3, 1, 5, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

        self.assertEqual(recurrence.next_scheduled, datetime(2014, 4, 1, 4, 3, 3))
        recurrence.update_schedule(recurrence.next_scheduled)

    def test_quarter(self):
        dt_in = datetime(2013, 4, 20, 12, 45, 48)
        td_in = timedelta(days=65, hours=3, minutes=3, seconds=3)
        interval_in = 'QUARTER'
        dt_expected = datetime(2013, 6, 5, 3, 3, 3)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_out, dt_expected)

    def test_quarterly_past(self):
        dt_in = datetime(2013, 6, 23, 0, 34, 55)
        td_in = timedelta(days=68, hours=16, minutes=30)
        interval_in = 'QUARTER'
        dt_expected = datetime(2013, 6, 8, 16, 30)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_expected, dt_out)

    def test_quarterly_overshoot(self):
        dt_in = datetime(2013, 1, 1, 0)
        td_in = timedelta(days=90, hours=12)
        interval_in = 'QUARTER'
        dt_expected = datetime(2013, 3, 31, 12)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_expected, dt_out)

    def test_quarterly_undershoot(self):
        dt_in = datetime(2013, 7, 1, 0)
        td_in = timedelta(days=90, hours=12)
        interval_in = 'QUARTER'
        dt_expected = datetime(2013, 9, 29, 12)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_expected, dt_out)

    def test_year(self):
        dt_in = datetime(2013, 6, 23, 0, 34, 55)
        td_in = timedelta(days=5, hours=16, minutes=30)
        interval_in = 'YEAR'
        dt_expected = datetime(2013, 1, 6, 16, 30)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_expected, dt_out)

    def test_year_end_leap_year(self):
        dt_in = datetime(2016, 6, 23, 0, 34, 55)
        td_in = timedelta(days=365, hours=16, minutes=30)
        interval_in = 'YEAR'
        dt_expected = datetime(2016, 12, 31, 16, 30)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_expected, dt_out)

    def test_year_end_non_leap_year(self):
        dt_in = datetime(2015, 6, 23, 0, 34, 55)
        td_in = timedelta(days=365, hours=16, minutes=30)
        interval_in = 'YEAR'
        dt_expected = datetime(2015, 12, 31, 16, 30)
        dt_out = _replace_with_offset(dt_in, td_in, interval_in)
        self.assertEqual(dt_expected, dt_out)

    def test_bad_interval(self):
        """
        A missformed interval should raise a value error
        """
        dt_in = datetime(2013, 1, 20, 12, 45, 48)
        td_in = timedelta(days=15, hours=3, minutes=3, seconds=3)
        interval_in = 'blah'
        with self.assertRaises(ValueError):
            _replace_with_offset(dt_in, td_in, interval_in)


class LocalizedRecurrenceUseTzSetting(TestCase):

    def test_with_and_without_use_tz(self):
        lr_with_use_tz = G(LocalizedRecurrence, timezone=pytz.timezone('US/Eastern'))
        lr_with_use_tz_utc = G(LocalizedRecurrence, timezone=pytz.UTC)
        with self.settings(USE_TZ=True, TIME_ZONE='UTC'):
            lr_with_use_tz.update_schedule()
            lr_with_use_tz_utc.update_schedule()
        self.assertTrue(timezone.is_aware(lr_with_use_tz.next_scheduled))
        self.assertTrue(timezone.is_aware(lr_with_use_tz_utc.next_scheduled))

        lr_without_use_tz = G(LocalizedRecurrence)
        with self.settings(USE_TZ=False):
            lr_without_use_tz.update_schedule()
        self.assertFalse(timezone.is_aware(lr_without_use_tz.next_scheduled))

        self.assertEqual(lr_with_use_tz_utc.next_scheduled.replace(tzinfo=None), lr_without_use_tz.next_scheduled)

    def test_prepare_datetime_field(self):
        self.assertIsNone(_prepare_datetime_field_value(None))
        naive_now = datetime.now()
        aware_now = naive_now.astimezone(pytz.timezone('US/Pacific'))
        with self.settings(USE_TZ=True):
            self.assertEqual(naive_now, _prepare_datetime_field_value(naive_now, make_aware=False))
            self.assertEqual(aware_now, _prepare_datetime_field_value(aware_now))

    def test_next_and_previous_scheduled_defaults(self):
        with self.settings(USE_TZ=True, TIME_ZONE='UTC'):
            lr = G(LocalizedRecurrence, timezone=pytz.timezone('US/Eastern'))
            self.assertEqual(lr.previous_scheduled, datetime(1970, 1, 1, tzinfo=pytz.UTC))
            self.assertEqual(lr.next_scheduled, datetime(1970, 1, 1, tzinfo=pytz.UTC))
        with self.settings(USE_TZ=True, TIME_ZONE='US/Pacific'):
            lr = G(LocalizedRecurrence, timezone=pytz.timezone('US/Eastern'))
            self.assertEqual(lr.previous_scheduled, datetime(1970, 1, 1, tzinfo=pytz.timezone('US/Pacific')))
            self.assertEqual(lr.next_scheduled, datetime(1970, 1, 1, tzinfo=pytz.timezone('US/Pacific')))
        with self.settings(USE_TZ=False, TIME_ZONE='US/Pacific'):
            lr = G(LocalizedRecurrence, timezone=pytz.timezone('US/Eastern'))
            self.assertEqual(lr.previous_scheduled, datetime(1970, 1, 1))
            self.assertEqual(lr.next_scheduled, datetime(1970, 1, 1))

    def test_database_with_or_without_tz_in_utc(self):
        scheduled_with_utc_tz = datetime(2018, 10, 10, tzinfo=pytz.UTC)
        scheduled_with_est_tz = datetime(2018, 10, 10, tzinfo=pytz.timezone('US/Eastern'))
        scheduled_without_tz = datetime(2018, 10, 10)
        # SQLite backend does not support timezone-aware datetimes when USE_TZ is False.
        with self.settings(USE_TZ=True, TIME_ZONE="UTC"):
            lr_with_utc_tz = G(LocalizedRecurrence, next_scheduled=scheduled_with_utc_tz,
                               previous_scheduled=scheduled_with_utc_tz, timezone=pytz.UTC)
            lr_with_est_tz = G(LocalizedRecurrence, next_scheduled=scheduled_with_est_tz,
                               previous_scheduled=scheduled_with_est_tz, timezone=pytz.timezone('US/Eastern'))
        lr_without_tz = G(LocalizedRecurrence, timezone=None, next_scheduled=scheduled_without_tz,
                          previous_scheduled=scheduled_without_tz)
        with self.settings(USE_TZ=True, TIME_ZONE="UTC"):
            self.assertEqual(lr_with_utc_tz.next_scheduled, lr_without_tz.next_scheduled.replace(tzinfo=pytz.UTC))
            self.assertEqual(lr_with_utc_tz.next_scheduled.replace(tzinfo=None),
                             lr_with_est_tz.next_scheduled.replace(tzinfo=None))

        with self.settings(USE_TZ=False):
            # Now make next_scheduled non-aware, and make sure that still works
            # (Django automatically converts non-aware to aware in the database)
            lr_with_utc_tz.previous_scheduled = datetime(2018, 10, 11)
            lr_with_utc_tz.next_scheduled = datetime(2018, 10, 11)
            lr_with_utc_tz.save()
            lr_with_utc_tz.refresh_from_db()
            self.assertEqual(lr_with_utc_tz.next_scheduled,
                             lr_without_tz.next_scheduled + timedelta(days=1))

            version = django.VERSION
            # assertWarns is only Django 2.1+
            if version[0] >= 2 and version[1] >= 1:  # pragma: no cover
                with self.settings(USE_TZ=True, TIME_ZONE="UTC"):
                    # Now make next_scheduled non-aware, and make sure that still works
                    with self.assertWarnsRegex(RuntimeWarning, r"DateTimeField LocalizedRecurrence\."
                                               r"(next|previous)\_scheduled "
                                               r"received a naive datetime \(2018-10-12 00:00:00\) "
                                               r"while time zone support is active\."):
                        lr_with_utc_tz.previous_scheduled = datetime(2018, 10, 12)
                        lr_with_utc_tz.next_scheduled = datetime(2018, 10, 12)
                        lr_with_utc_tz.save()
                    lr_with_utc_tz.refresh_from_db()
                    self.assertEqual(lr_with_utc_tz.next_scheduled.replace(tzinfo=None),
                                     lr_without_tz.next_scheduled + timedelta(days=2))
