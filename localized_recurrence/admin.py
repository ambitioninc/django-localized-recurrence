from django.contrib.admin import ModelAdmin, site

from localized_recurrence.models import LocalizedRecurrence


class LocalizedRecurrenceAdmin(ModelAdmin):
    list_display = [
        'id',
        'interval',
        'timezone',
        'offset',
        'previous_scheduled',
        'next_scheduled',
    ]


site.register(LocalizedRecurrence, LocalizedRecurrenceAdmin)
