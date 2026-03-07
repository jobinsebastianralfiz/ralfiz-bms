from django.db import migrations


def create_leave_types(apps, schema_editor):
    LeaveType = apps.get_model('employees', 'LeaveType')
    defaults = [
        ('Casual Leave', 12, True),
        ('Sick Leave', 10, True),
        ('Earned Leave', 15, True),
    ]
    for name, days, is_paid in defaults:
        LeaveType.objects.get_or_create(
            name=name,
            defaults={'days_allowed': days, 'is_paid': is_paid, 'is_active': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_leave_types, migrations.RunPython.noop),
    ]