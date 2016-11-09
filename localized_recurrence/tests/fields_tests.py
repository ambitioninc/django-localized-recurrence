import unittest
from datetime import timedelta

import django
import six
if six.PY3:  # pragma: no cover
    from importlib import reload

from mock import MagicMock, patch

from .. import fields


class DurationFieldToPythonTest(unittest.TestCase):
    def setUp(self):
        """Create a mock of the DurationField class and pin to_python to it.
        """
        self.df = fields.DurationField()
        self.df_with_default = fields.DurationField(default=60)

    def test_deconstruct_with_default(self):
        """
        Test .deconstruct() with a default
        """
        if django.VERSION[1] >= 7:  # pragma: no cover
            name, path, args, kwargs = self.df_with_default.deconstruct()

            self.assertEqual(kwargs['default'], 60)
        else:  # pragma: no cover
            with patch('localized_recurrence.fields.IntegerField.deconstruct', create=True) as mock_deconstruct:
                mock_deconstruct.return_value = (
                    'duration', 'django.db.models.IntegerField', [], {'default': timedelta(seconds=60)}
                )
                name, path, args, kwargs = self.df_with_default.deconstruct()
                self.assertEqual(kwargs['default'], 60)

    def test_deconstruct_without_default(self):
        """
        Test .deconstruct() without a default
        """
        if django.VERSION[1] >= 7:  # pragma: no cover
            name, path, args, kwargs = self.df.deconstruct()
            self.assertFalse('default' in kwargs.keys())
        else:  # pragma: no cover
            with patch('localized_recurrence.fields.IntegerField.deconstruct', create=True) as mock_deconstruct:
                mock_deconstruct.return_value = (
                    'duration', 'django.db.models.IntegerField', [], {}
                )
                name, path, args, kwargs = self.df_with_default.deconstruct()
                self.assertNotIn('default', kwargs.keys())

    def test_timedelta(self):
        """A timedelta should just get returned.
        """
        td_in = timedelta(days=1, hours=3)
        td_out = self.df.to_python(td_in)
        self.assertEqual(td_out, td_in)

    def test_string(self):
        """A string should be properly converted.
        """
        td_expected = timedelta(days=3, hours=5, minutes=10)
        str_in = str(td_expected)
        td_out = self.df.to_python(str_in)
        self.assertEqual(td_out, td_expected)

    def test_bad_string(self):
        """Malformed strings should raise an error.
        """
        str_in = "3:5"
        with self.assertRaises(ValueError):
            self.df.to_python(str_in)

    def test_int(self):
        """Int inputs should give timedelta outputs
        """
        int_in = 176400
        td_expected = timedelta(days=2, hours=1)
        td_out = self.df.to_python(int_in)
        self.assertEqual(td_out, td_expected)

    def test_none(self):
        """Null input -> None output
        """
        td_in = None
        td_out = self.df.to_python(td_in)
        self.assertEqual(td_in, td_out)

    def test_invalid(self):
        """Unsupported objects raise ValueError
        """
        td_in = self
        with self.assertRaises(ValueError):
            self.df.to_python(td_in)


class DurationFieldGetPrepValueTest(unittest.TestCase):
    def setUp(self):
        """Create a mock of the DurationField class and pin get_prep_value.
        """
        self.df = fields.DurationField()

    def test_returns_int(self):
        """Type should be `int`.
        """
        td_in = timedelta(hours=14)
        int_out = self.df.get_prep_value(td_in)
        self.assertTrue(isinstance(int_out, int))

    def test_returns_int2(self):
        """Type should be `int`.
        """
        td_in = timedelta(hours=14, seconds=3.5)
        int_out = self.df.get_prep_value(td_in)
        self.assertTrue(isinstance(int_out, int))

    def test_round_trip(self):
        """A trip through get_prep_value and to_python.
        """
        td_in = timedelta(hours=14)
        int_out = self.df.get_prep_value(td_in)
        td_out = self.df.to_python(int_out)
        self.assertEqual(td_out, td_in)


class DurationFieldValueToStringTest(unittest.TestCase):
    def setUp(self):
        """Create a mock of the DurationField class and pin value_to_string to it.

        We also mock out the _get_val_from_obj, to just return what is
        passed in. Allows us to pass in a timedelta for testing intead
        of the expected object.
        """
        self.mock_DurationField = MagicMock()
        self.mock_DurationField.value_to_string = fields.DurationField.__dict__['value_to_string']
        self.mock_DurationField.to_python = fields.DurationField.__dict__['to_python']
        self.mock_DurationField._get_val_from_obj.side_effect = lambda x: x

    def test_simple_string(self):
        """
        """
        in_td = timedelta(days=1, hours=1, minutes=1, seconds=1)
        expected_str = "1 day, 1:01:01"
        out_str = self.mock_DurationField.value_to_string(self.mock_DurationField, in_td)
        self.assertEqual(out_str, expected_str)

    def test_loop_to_python(self):
        """A roundtrip through value_to_string and to_python.

        We expect the value to be unchanged after the trip.
        """
        in_td = timedelta(days=1, hours=1, minutes=1, seconds=1)
        out_str = self.mock_DurationField.value_to_string(self.mock_DurationField, in_td)
        out_td = self.mock_DurationField.to_python(self.mock_DurationField, out_str)
        self.assertEqual(out_td, in_td)


class ParseTimedeltaStringTest(unittest.TestCase):
    """Test some round trips between timedelta, string, timedelta.
    """
    def test_works(self):
        """Test a bunch of cases for the regular expressions.

        We test so many things in this test because regular
        expressions represent a lot of effective branching.
        """
        td1_in = timedelta(days=1)
        td2_in = timedelta(seconds=1)
        td3_in = timedelta(hours=1, minutes=1, seconds=1)
        td4_in = timedelta(days=1, seconds=10000.001)
        td5_in = timedelta(hours=12)
        td6_in = timedelta(hours=-12)
        str1_out = str(td1_in)
        str2_out = str(td2_in)
        str3_out = str(td3_in)
        str4_out = str(td4_in)
        str5_out = str(td5_in)
        str6_out = str(td6_in)
        td1_out = fields.parse_timedelta_string(str1_out)
        td2_out = fields.parse_timedelta_string(str2_out)
        td3_out = fields.parse_timedelta_string(str3_out)
        td4_out = fields.parse_timedelta_string(str4_out)
        td5_out = fields.parse_timedelta_string(str5_out)
        td6_out = fields.parse_timedelta_string(str6_out)
        self.assertEqual(td1_in, td1_out)
        self.assertEqual(td2_in, td2_out)
        self.assertEqual(td3_in, td3_out)
        self.assertEqual(td4_in, td4_out)
        self.assertEqual(td5_in, td5_out)
        self.assertEqual(td6_in, td6_out)


class SetupSouthTest(unittest.TestCase):
    def test_no_south(self):
        """This test is meant to hit the branch handleing the ImportError for
        south.

        Some users may not have south, so if it is not available, we
        just pass.
        """
        with patch.dict('sys.modules', {'south.modelsinspector': {}}):
            reload(fields)
