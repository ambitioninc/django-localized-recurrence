from datetime import timedelta
import re

from django.db.models.fields import IntegerField
import six


class CastOnAssignDescriptor(object):
    """
    A property descriptor which ensures that `field.to_python()` is called on _every_ assignment to the field.
    This used to be provided by the `django.db.models.subclassing.Creator` class, which in turn
    was used by the deprecated-in-Django-1.10 `SubfieldBase` class, hence the reimplementation here.
    https://stackoverflow.com/questions/39392343/
    how-do-i-make-a-custom-model-field-call-to-python-when-the-field-is-accessed-imm
    """

    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):  # pragma: no cover
        if obj is None:
            return self
        return obj.__dict__[self.field.name]

    def __set__(self, obj, value):  # pragma: no cover
        obj.__dict__[self.field.name] = self.field.to_python(value)


class DurationField(IntegerField):
    """A field to store durations of time with accuracy to the second.

    A Duration Field will automatically convert between python
    timedelta objects and database integers.

    Duration fields can be used to define fields in a django model

    .. code-block:: python

        class Presentations(models.Model):
            length = DurationField()
            speaker = models.ForeignKey(User)
            location = models.ForeignKey(Location)

    Given such a model, storing a duration in the database is as
    simple as passing in a ``timedelta`` object

    .. code-block:: python

        >>> Presentations.objects.create(
        ...     length=datetime.timedelta(minutes=45),
        ...     speaker=User.objects.get(email='MrT@example.com'),
        ...     location=wrestle_mania_ring,
        ... )

    The timedeltas are stored as seconds in the backend, so sub-second
    accuracy is lost with this field.

    """
    description = "A duration of time."

    def __init__(self, *args, **kwargs):
        """Call out to the super. Makes docs cleaner."""
        return super(DurationField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(DurationField, self).contribute_to_class(cls, name)
        setattr(cls, name, CastOnAssignDescriptor(self))

    def to_python(self, value):
        """Convert a stored duration into a python datetime.timedelta object.

        Need to handle three cases:
            - An instance of the correct type (timedelta).
            - A string (e.g., from a deserializer).
            - What the database returns (integer).
        """
        if isinstance(value, timedelta):
            v = value
        elif isinstance(value, (six.binary_type, six.text_type)):
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

    def deconstruct(self):
        name, path, args, kwargs = super(DurationField, self).deconstruct()
        if 'default' in kwargs.keys():
            kwargs['default'] = self.get_prep_value(kwargs['default'])
        return name, 'localized_recurrence.fields.DurationField', args, kwargs

    def get_prep_value(self, value):
        """Convert a timedelta to integer for storage.
        """
        value = self.to_python(value)
        return int(value.total_seconds())

    def value_to_string(self, obj):
        """Used by serializers to get a string representation.
        """
        time_delta_value = self._get_val_from_obj(obj)
        return str(time_delta_value)


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
