"""Seed the Internship Continuation & Learning Agreement template.

Text transcribed verbatim from Ralfiz_Internship_Continuation_Agreement.pdf.
Re-running updates the existing v1.0 row rather than creating duplicates;
pass --force to overwrite a template that HR has since edited.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from employees.models import AgreementTemplate

NAME = 'Internship Continuation & Learning Agreement'
VERSION = 'v1.0'

INTRO = (
    "Dear Intern,\n"
    "As part of our internship program, we would like to confirm whether you wish to continue "
    "your internship with Ralfiz Technologies. The internship is designed to provide practical "
    "exposure, structured guidance, work-related learning materials, and opportunities to develop "
    "your technical and professional skills.\n"
    "Please review the following terms and confirm your decision to continue."
)

SECTIONS = [
    {
        'no': 1,
        'title': 'Internship Continuation',
        'body': 'I confirm that I would like to:',
        'bullets': [],
        'footnote': 'If you choose to continue, you agree to follow the internship policies and '
                    'guidelines mentioned in this document.',
    },
    {
        'no': 2,
        'title': 'Monthly Internship Fee',
        'body': 'The fee supports the structured learning and guidance provided during the internship, including:',
        'show_fee': True,
        # Used instead when the internship carries no fee.
        'title_free': 'Learning Support & Guidance',
        'body_free': 'This internship carries no monthly fee. The structured learning and guidance '
                     'provided during the internship includes:',
        'bullets': [
            'Guidance and mentorship for assigned work',
            'Work-related learning materials and resources',
            'Technical guidance to improve practical skills',
            'Support and direction while completing assigned tasks',
            'Learning resources relevant to the internship domain',
            'Practical exposure through assigned projects and activities',
        ],
    },
    {
        'no': 3,
        'title': 'Internship Schedule & Holidays',
        'body': 'For interns who are currently attending college, the following schedule will apply:',
        'bullets': [
            'Saturday and Sunday will be treated as holidays',
            'College-declared holidays, public holidays, and other applicable holidays will be treated '
            'as holidays for the internship, subject to the company’s schedule and prior communication',
        ],
        'footnote': 'Interns are expected to attend and participate on the regular working days unless '
                    'prior permission or an approved leave is obtained.',
    },
    {
        'no': 4,
        'title': 'Attendance & Punctuality',
        'body': 'Interns are expected to:',
        'bullets': [
            'Maintain regular attendance',
            'Be punctual for scheduled internship activities',
            'Inform the concerned coordinator in advance when unable to attend',
            'Complete assigned work within the given deadlines',
            'Participate actively in training, meetings, discussions, and project activities',
        ],
        'footnote': 'Repeated absence without prior communication may affect the continuation of the internship.',
    },
    {
        'no': 5,
        'title': 'Work & Learning Responsibilities',
        'body': 'During the internship, interns may receive practical assignments, projects, exercises, '
                'and learning activities. Interns are expected to:',
        'bullets': [
            'Complete assigned tasks responsibly',
            'Follow the instructions provided by mentors or coordinators',
            'Make genuine efforts to learn and improve',
            'Ask questions whenever clarification is required',
            'Submit work within the assigned timelines',
            'Maintain professional communication with the team',
        ],
        'footnote': 'The guidance provided is intended to help interns learn and complete their work; '
                    'interns are expected to make their own effort to understand and implement the assigned tasks.',
    },
    {
        'no': 6,
        'title': 'Learning Materials',
        'body': 'Ralfiz Technologies may provide learning materials, references, documentation, examples, '
                'assignments, and other resources relevant to the internship.',
        'bullets': [],
        'callout': {
            'style': 'warn',
            'text': 'Such materials are provided for educational and internship purposes only and should not '
                    'be redistributed, published, or commercially used without appropriate permission.',
        },
    },
    {
        'no': 7,
        'title': 'Professional Conduct',
        'body': 'All interns are expected to maintain professional behaviour throughout the internship. Interns must:',
        'bullets': [
            'Communicate respectfully with mentors, employees, and other interns',
            'Follow company policies and instructions',
            'Protect confidential company information',
            'Avoid inappropriate or unprofessional behaviour',
            'Respect project deadlines and responsibilities',
        ],
        'footnote': 'Any serious violation of company policies may result in termination of the internship.',
    },
    {
        'no': 8,
        'title': 'Confidentiality',
        'body': 'Any company information, project information, source code, documents, credentials, business '
                'information, client information, or other confidential materials shared during the internship '
                'must be kept confidential. Interns must not share or publish confidential information without '
                'prior authorization from Ralfiz Technologies.',
        'bullets': [],
    },
    {
        'no': 9,
        'title': 'Completion & Continuation',
        'body': 'Continuation of the internship is subject to:',
        'bullets': [
            'Regular attendance',
            'Satisfactory participation',
            'Completion of assigned work',
            'Professional conduct',
            'Compliance with internship policies and terms',
            'Timely payment of the applicable monthly fee',
        ],
        'bullets_free': [
            'Regular attendance',
            'Satisfactory participation',
            'Completion of assigned work',
            'Professional conduct',
            'Compliance with internship policies and terms',
        ],
        'footnote': 'The company reserves the right to discontinue an internship where there is continued '
                    'non-compliance, poor participation, misconduct, or other legitimate reasons.',
    },
]

CONFIRMATION = (
    'By selecting <strong>Continue my internship</strong>, I confirm that I have read and understood the '
    'above terms and conditions. I agree to follow the internship policies, maintain regular participation, '
    'complete assigned work, and pay the applicable monthly internship fee for continued participation.'
)

CONFIRMATION_FREE = (
    'By selecting <strong>Continue my internship</strong>, I confirm that I have read and understood the '
    'above terms and conditions. I agree to follow the internship policies, maintain regular participation, '
    'and complete assigned work for continued participation.'
)


class Command(BaseCommand):
    help = 'Create or refresh the Internship Continuation & Learning Agreement template.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Overwrite the existing template even if it has been edited.')

    def handle(self, *args, **options):
        defaults = {
            'agreement_type': 'internship_continuation',
            'heading': 'Internship Continuation & Learning Agreement',
            'eyebrow': 'INTERNSHIP CONTINUATION CONFIRMATION',
            'intro_html': INTRO,
            'sections': SECTIONS,
            'monthly_fee': Decimal('750.00'),
            'fee_in_words': 'Rupees Seven Hundred and Fifty only',
            'fee_note': 'applicable for each month of continued participation',
            'confirmation_html': CONFIRMATION,
            'confirmation_free_html': CONFIRMATION_FREE,
            'continue_label': 'Continue my internship',
            'decline_label': 'Discontinue my internship',
            'require_college_fields': True,
            'is_active': True,
        }

        existing = AgreementTemplate.objects.filter(name=NAME, version=VERSION).first()
        if existing and not options['force']:
            if existing.updated_at > existing.created_at:
                self.stdout.write(self.style.WARNING(
                    f'Template "{NAME}" {VERSION} exists and has been edited since creation. '
                    'Left untouched - pass --force to overwrite.'
                ))
                return
            for key, value in defaults.items():
                setattr(existing, key, value)
            existing.save()
            self.stdout.write(self.style.SUCCESS(f'Refreshed template: {existing}'))
            return

        template, created = AgreementTemplate.objects.update_or_create(
            name=NAME, version=VERSION, defaults=defaults,
        )
        verb = 'Created' if created else 'Overwrote'
        self.stdout.write(self.style.SUCCESS(f'{verb} template: {template}'))
