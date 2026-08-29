"""Seed the Internship Continuation & Learning Agreement template.

Runs on deploy so the HR send screen is usable immediately. Idempotent: it
skips if a template with the same name and version already exists, and the
`seed_internship_agreement` management command remains the way to refresh it.
"""
from django.db import migrations


def seed_template(apps, schema_editor):
    from decimal import Decimal

    from employees.management.commands.seed_internship_agreement import (
        CONFIRMATION, INTRO, NAME, SECTIONS, VERSION,
    )

    AgreementTemplate = apps.get_model('employees', 'AgreementTemplate')
    if AgreementTemplate.objects.filter(name=NAME, version=VERSION).exists():
        return

    AgreementTemplate.objects.create(
        name=NAME,
        version=VERSION,
        agreement_type='internship_continuation',
        heading='Internship Continuation & Learning Agreement',
        eyebrow='INTERNSHIP CONTINUATION CONFIRMATION',
        intro_html=INTRO,
        sections=SECTIONS,
        monthly_fee=Decimal('750.00'),
        fee_in_words='Rupees Seven Hundred and Fifty only',
        fee_note='applicable for each month of continued participation',
        confirmation_html=CONFIRMATION,
        continue_label='Continue my internship',
        decline_label='Discontinue my internship',
        require_college_fields=True,
        is_active=True,
    )


def unseed_template(apps, schema_editor):
    from employees.management.commands.seed_internship_agreement import NAME, VERSION

    AgreementTemplate = apps.get_model('employees', 'AgreementTemplate')
    # Only remove it if nobody has been sent this agreement yet.
    template = AgreementTemplate.objects.filter(name=NAME, version=VERSION).first()
    if template and not template.requests.exists():
        template.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0024_agreementtemplate_agreementrequest'),
    ]

    operations = [
        migrations.RunPython(seed_template, unseed_template),
    ]
