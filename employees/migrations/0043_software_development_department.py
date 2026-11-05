"""Undo 0042: Software Development is its own area and department, next to Engineering."""
from django.db import migrations, models

OLD, NEW = 'Engineering', 'Software Development'


def restore(apps, schema_editor):
    # 0042 (deployed earlier the same day) renamed every "Software Development" to
    # "Engineering". Put the area back and point it at the new department.
    Settings = apps.get_model('employees', 'EnrolmentSettings')
    for s in Settings.objects.all():
        tracks = s.tracks or []
        labels = {(t.get('label') or '').strip().casefold() for t in tracks if isinstance(t, dict)}
        changed = False
        for t in tracks:
            if not isinstance(t, dict):
                continue
            label = (t.get('label') or '').strip().casefold()
            if label == OLD.casefold() and NEW.casefold() not in labels:
                t['label'], t['department'] = NEW, 'software'
                changed = True
            elif label == NEW.casefold() and t.get('department') != 'software':
                t['department'] = 'software'
                changed = True
        if changed:
            s.tracks = tracks
            s.save(update_fields=['tracks'])

    Enrolment = apps.get_model('employees', 'InternEnrolment')
    Enrolment.objects.filter(track__iexact=OLD).update(track=NEW)

    Employee = apps.get_model('employees', 'Employee')
    Employee.objects.filter(designation__iexact='Engineering Intern').update(designation='Software Development Intern')


class Migration(migrations.Migration):
    dependencies = [('employees', '0042_rename_software_development_track')]
    operations = [
        migrations.AlterField(
            model_name='employee', name='department',
            field=models.CharField(choices=[
                ('engineering', 'Engineering'), ('software', 'Software Development'),
                ('design', 'Design'), ('marketing', 'Marketing'), ('sales', 'Sales'),
                ('hr', 'Human Resources'), ('operations', 'Operations'),
                ('finance', 'Finance'), ('other', 'Other')],
                default='engineering', max_length=20),
        ),
        migrations.RunPython(restore, migrations.RunPython.noop),
    ]
