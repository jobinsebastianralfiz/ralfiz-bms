"""Seed the Internship Agreement template used for new joiners.

The continuation agreement (seed_internship_agreement) asks an intern already
with us whether to carry on. This one is the document a new joiner signs when
they accept a place: it states the period and renewal terms, the stipend, the
policies they are agreeing to, and how a job offer is considered at the end.

Sections 4-9 are the continuation agreement's wording, which applies to any
intern regardless of when they joined. Sections 1, 2, 3, 10 and 11 are new.

Re-running updates the existing v1.0 row rather than creating duplicates;
pass --force to overwrite a template that HR has since edited.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from employees.models import AgreementTemplate

NAME = 'Internship Agreement - New Joinee'
VERSION = 'v1.0'

INTRO = (
    "Dear Intern,\n"
    "We are glad to confirm your place in the Ralfiz Technologies internship program. "
    "The internship is designed to provide practical exposure, structured guidance, "
    "work-related learning materials, and opportunities to develop your technical and "
    "professional skills.\n"
    "Please review the terms below and confirm whether you accept this internship."
)

SECTIONS = [
    {
        'no': 1,
        'title': 'Internship Offer',
        'body': 'Ralfiz Technologies offers you a place in its internship program. I confirm that I would like to:',
        'bullets': [],
        'footnote': 'By accepting, you agree to follow the internship policies and guidelines set out in '
                    'this document for the whole of the internship period.',
    },
    {
        'no': 2,
        'title': 'Internship Period & Renewal',
        'body': 'The internship runs for the period communicated to you in writing at the time of joining. '
                'On the terms of renewal:',
        'bullets': [
            'The internship period, start date and reporting location are as communicated to you separately in writing',
            'The internship may be renewed for a further period by mutual agreement, in writing',
            'Renewal is considered on attendance, participation, completed work and professional conduct',
            'A renewal is confirmed through a fresh Internship Continuation Agreement, which supersedes this one for the renewed period',
            'Neither party is obliged to renew, and a decision not to renew does not affect the certificate '
            'issued for the period already completed',
        ],
        'footnote': 'Either party may end the internship before the end of the period by giving reasonable '
                    'notice in writing to the other.',
    },
    {
        'no': 3,
        'title': 'Monthly Stipend',
        # title/body/bullets here are a fallback; build_snapshot swaps in the
        # wording for whichever arrangement HR picks when sending.
        'body': 'A monthly stipend is payable to you for the duration of the internship, subject to the '
                'conditions below:',
        'show_fee': True,
        # Used instead when the internship carries no stipend.
        'title_free': 'Learning Support & Guidance',
        'body_free': 'This internship carries no monthly stipend. The structured learning and guidance '
                     'provided during the internship includes:',
        'bullets': [
            'The stipend is paid monthly in arrears, for the days actually attended',
            'The stipend is a contribution towards the cost of attending and is not a salary or wage',
            'Payment is subject to satisfactory attendance and participation for the month',
            'Any deduction for unapproved absence will be communicated to you before it is applied',
            'The stipend may be revised at renewal, in writing',
        ],
        'bullets_free': [
            'Guidance and mentorship for assigned work',
            'Work-related learning materials and resources',
            'Technical guidance to improve practical skills',
            'Support and direction while completing assigned tasks',
            'Learning resources relevant to the internship domain',
            'Practical exposure through assigned projects and activities',
        ],
    },
    {
        'no': 4,
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
        'no': 5,
        'title': 'Attendance & Punctuality',
        'body': 'Interns are expected to:',
        'bullets': [
            'Maintain regular attendance',
            'Be punctual for scheduled internship activities',
            'Inform the concerned coordinator in advance when unable to attend',
            'Complete assigned work within the given deadlines',
            'Participate actively in training, meetings, discussions, and project activities',
        ],
        'footnote': 'Repeated absence without prior communication may affect the stipend for the month and '
                    'the continuation of the internship.',
    },
    {
        'no': 6,
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
        'no': 7,
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
        'no': 8,
        'title': 'Company Policy & Professional Conduct',
        'body': 'All interns are expected to maintain professional behaviour throughout the internship and '
                'to follow the company policies in force from time to time. Interns must:',
        'bullets': [
            'Communicate respectfully with mentors, employees, other interns, and clients',
            'Follow company policies, instructions, and the attendance and leave process',
            'Protect confidential company information',
            'Avoid inappropriate or unprofessional behaviour, including on company communication channels',
            'Respect project deadlines and responsibilities',
            'Use company devices, accounts, and credentials only for assigned work',
        ],
        'footnote': 'Any serious violation of company policies may result in termination of the internship '
                    'without notice, and the stipend for the period concerned may be withheld.',
    },
    {
        'no': 9,
        'title': 'Confidentiality & Ownership of Work',
        'body': 'Any company information, project information, source code, documents, credentials, business '
                'information, client information, or other confidential materials shared during the internship '
                'must be kept confidential. Interns must not share or publish confidential information without '
                'prior authorization from Ralfiz Technologies.',
        'bullets': [
            'Confidentiality continues to apply after the internship ends',
            'Work produced as part of assigned tasks belongs to Ralfiz Technologies or its clients',
            'Work may be shown in a personal portfolio only with prior written permission',
        ],
    },
    {
        'no': 10,
        'title': 'Performance Review & Job Offer',
        'body': 'Interns are reviewed during and at the end of the internship. On employment after the internship:',
        'bullets': [
            'Performance is reviewed on completed work, attendance, learning, and professional conduct',
            'Interns who complete the internship satisfactorily may be considered for a role at Ralfiz Technologies',
            'Any such offer depends on a suitable opening being available and on the company’s hiring decision at that time',
            'An offer of employment, if made, will be issued separately in writing on its own terms',
            'Completing this internship does not by itself create any offer, promise, or guarantee of employment',
        ],
        'footnote': 'This agreement is an internship and training arrangement. It does not create a contract '
                    'of employment between you and Ralfiz Technologies.',
    },
    {
        'no': 11,
        'title': 'Completion & Certificate',
        'body': 'Successful completion of the internship is subject to:',
        'bullets': [
            'Regular attendance',
            'Satisfactory participation',
            'Completion of assigned work',
            'Professional conduct',
            'Compliance with internship policies and terms',
        ],
        'footnote': 'A certificate is issued on satisfactory completion of the internship period. The company '
                    'reserves the right to discontinue an internship where there is continued non-compliance, '
                    'poor participation, misconduct, or other legitimate reasons.',
    },
]

CONFIRMATION = (
    'By selecting <strong>Accept the internship</strong>, I confirm that I have read and understood the '
    'above terms and conditions. I agree to follow the internship policies, maintain regular participation, '
    'complete assigned work, and accept the monthly stipend on the terms set out above. I understand that '
    'this internship does not by itself create an offer of employment.'
)

CONFIRMATION_FREE = (
    'By selecting <strong>Accept the internship</strong>, I confirm that I have read and understood the '
    'above terms and conditions. I agree to follow the internship policies, maintain regular participation, '
    'and complete assigned work. I understand that this internship does not by itself create an offer of '
    'employment.'
)


class Command(BaseCommand):
    help = 'Create or refresh the Internship Agreement template for new joiners.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Overwrite the existing template even if it has been edited.')
        parser.add_argument('--stipend', default='0',
                            help='Default monthly stipend. 0 means the template carries none; '
                                 'HR can still set an amount per person when sending.')

    def handle(self, *args, **options):
        say = self.stdout.write if options.get('verbosity', 1) else lambda *a, **k: None
        stipend = Decimal(options['stipend'])
        defaults = {
            'agreement_type': 'internship_new_joinee',
            'heading': 'Internship Agreement',
            'eyebrow': 'INTERNSHIP CONFIRMATION',
            'intro_html': INTRO,
            'sections': SECTIONS,
            'money_mode': 'stipend',
            'monthly_fee': stipend if stipend > 0 else None,
            'fee_note': 'payable monthly for the days attended',
            'confirmation_html': CONFIRMATION,
            'confirmation_free_html': CONFIRMATION_FREE,
            'continue_label': 'Accept the internship',
            'decline_label': 'Decline the internship',
            'decision_heading': 'Internship Offer Decision',
            'accept_sub': 'join Ralfiz Technologies as an intern',
            'decline_sub': 'do not take up this internship',
            'accept_statement': 'I accept the internship offered by Ralfiz Technologies',
            'decline_statement': 'I do not wish to take up this internship',
            'accept_confirm_text': 'I confirm I have read and understood the terms, and I accept this '
                                   'internship with Ralfiz Technologies',
            'decline_heading': 'Decline the Internship',
            'decline_intro': 'You are about to inform Ralfiz Technologies that you do not wish to take up '
                             'this internship.',
            'decline_button_label': 'Confirm my decision',
            'require_college_fields': True,
            'is_active': True,
        }

        template = AgreementTemplate.objects.filter(name=NAME, version=VERSION).first()
        if template is None:
            AgreementTemplate.objects.create(name=NAME, version=VERSION, **defaults)
            say(self.style.SUCCESS(f'Created "{NAME}" {VERSION}.'))
            return

        if not options['force']:
            say(self.style.WARNING(
                f'"{NAME}" {VERSION} already exists. Pass --force to overwrite HR\'s edits.'))
            return

        for field, value in defaults.items():
            setattr(template, field, value)
        template.save()
        say(self.style.SUCCESS(f'Updated "{NAME}" {VERSION}.'))
