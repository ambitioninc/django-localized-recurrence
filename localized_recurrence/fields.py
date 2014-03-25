from datetime import timedelta
import re

from django.db.models import SubfieldBase
from django.db.models.fields import IntegerField


class DurationField(IntegerField):
    """A field to store durations of time with accuracy to the second.

    Automatically converts between python timedelta objects and
    database integers.

    The timedeltas are stored as seconds in the backend, so sub-second
    accuracy is lost with this field.
    """
    description = "A duration of time."
    __metaclass__ = SubfieldBase

    def to_python(self, value):
        """Convert a stored duration into a python datetime.timedelta object.

        Need to handle three cases:
            - An instance of the correct type (timedelta).
            - A string (e.g., from a deserializer).
            - What the database returns (integer).
        """
        if isinstance(value, timedelta):
            v = value
        elif isinstance(value, (str, unicode)):
            # The string should be in the form "[D day[s],][H]H:MM:SS[.UUUUUU]"
            try:
                v = parse_timedelta_string(value)
            except ValueError:
                raise ValueError("Duration string must be in the form '[D day[s],][H]H:MM:SS[.UUUUUU]'")
        elif isinstance(value, int):
            v = timedelta(seconds=value)
        elif value is None:
            v = None
        else:
            raise ValueError("Not a valid Duration object")
        return v

    def get_prep_value(self, value):
        """Convert a timedelta to integer for storage.
        """
        # import pdb; pdb.set_trace()
        value = self.to_python(value)
        return int(value.total_seconds())

    def value_to_string(self, obj):
        """Used by serializers to get a string representation.
        """
        time_delta_value = self._get_val_from_obj(obj)
        return time_delta_value.__str__()


def parse_timedelta_string(string):
    """Parses strings from datetime.timedelta.__str__.

    Usefull because django's force_text uses .__str__ instead of
    .__repr__

    datetime.timedelta.__str__ returns a string in the form [D day[s],
    ][H]H:MM:SS[.UUUUUU], where D is negative for negative t.
    """
    days_re = "(?P<days>-?[0-9]*) days?, (?P<hours>[0-9]+):(?P<minutes>[0-9]+):(?P<seconds>[0-9]+\.?[0-9]*)"
    no_days_re = "(?P<hours>[0-9]+):(?P<minutes>[0-9]+):(?P<seconds>[0-9]+\.?[0-9]*)"
    match_days = re.match(days_re, string)
    match_no_days = re.match(no_days_re, string)
    if match_days:
        return timedelta(**{k: float(v) for k, v in match_days.groupdict().items()})
    elif match_no_days:
        return timedelta(**{k: float(v) for k, v in match_no_days.groupdict().items()})
    else:
        raise ValueError("'%s' is not in the form [D day[s],][H]H:MM:SS[.UUUUUU]" % string)


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^localized_recurrence\.fields\.DurationField"])
except ImportError:
    pass
