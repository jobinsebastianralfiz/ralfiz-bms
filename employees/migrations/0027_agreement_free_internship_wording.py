"""Teach the already-seeded agreement template about free internships.

0025 seeded wording that hardcoded the Rs.750 fee, which is wrong for an
intern on a free internship. This adds the fee-free variants and de-hardcodes
the amount, without trampling wording that HR has since edited by hand.
"""
from django.db import migrations


def add_free_wording(apps, schema_editor):
    from employees.management.commands.seed_internship_agreement import (
        CONFIRMATION, CONFIRMATION_FREE, NAME, SECTIONS,
    )

    AgreementTemplate = apps.get_model('employees', 'AgreementTemplate')

    # Section variants, keyed by section number, from the current seed.
    variants = {
        section['no']: {
            key: section[key]
            for key in ('title_free', 'body_free', 'bullets_free')
            if key in section
        }
        for section in SECTIONS
    }

    for template in AgreementTemplate.objects.filter(name=NAME):
        changed = False

        if not template.confirmation_free_html:
            template.confirmation_free_html = CONFIRMATION_FREE
            changed = True

        # Only rewrite the paid confirmation if it is still the original text
        # with the amount baked in - an edited one is left alone.
        if '750' in (template.confirmation_html or '') and 'monthly internship fee' in (template.confirmation_html or ''):
            template.confirmation_html = CONFIRMATION
            changed = True

        sections = template.sections or []
        for section in sections:
            for key, value in variants.get(section.get('no'), {}).items():
                if key not in section:
                    section[key] = value
                    changed = True
        if changed:
            template.sections = sections
            template.save()


def remove_free_wording(apps, schema_editor):
    from employees.management.commands.seed_internship_agreement import NAME

    AgreementTemplate = apps.get_model('employees', 'AgreementTemplate')
    for template in AgreementTemplate.objects.filter(name=NAME):
        sections = template.sections or []
        for section in sections:
            for key in ('title_free', 'body_free', 'bullets_free'):
                section.pop(key, None)
        template.sections = sections
        template.confirmation_free_html = ''
        template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0026_agreementtemplate_confirmation_free_html'),
    ]

    operations = [
        migrations.RunPython(add_free_wording, remove_free_wording),
    ]
