"""Ralfiz has an Engineering area, not "Software Development": rename it wherever it was saved."""
from django.db import migrations

OLD, NEW = 'Software Development', 'Engineering'


def rename(apps, schema_editor):
    Settings = apps.get_model('employees', 'EnrolmentSettings')
    for s in Settings.objects.all():
        tracks = s.tracks or []
        changed = False
        for t in tracks:
            if isinstance(t, dict) and (t.get('label') or '').strip().casefold() == OLD.casefold():
                t['label'] = NEW
                changed = True
        if changed:
            s.tracks = tracks
            s.save(update_fields=['tracks'])

    Enrolment = apps.get_model('employees', 'InternEnrolment')
    Enrolment.objects.filter(track__iexact=OLD).update(track=NEW)

    Employee = apps.get_model('employees', 'Employee')
    for e in Employee.objects.filter(designation__icontains=OLD):
        e.designation = e.designation.replace(OLD, NEW).replace(OLD.lower(), NEW)
        e.save(update_fields=['designation'])


class Migration(migrations.Migration):
    dependencies = [('employees', '0041_holiday_source_label')]
    operations = [migrations.RunPython(rename, migrations.RunPython.noop)]
