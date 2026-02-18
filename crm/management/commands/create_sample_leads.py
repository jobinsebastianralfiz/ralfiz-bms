from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from crm.models import InternProfile, Lead, LeadNote, DailyActivity, Demo


class Command(BaseCommand):
    help = 'Create sample CRM data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample CRM data...\n')

        # Create admin user if not exists
        admin, created = User.objects.get_or_create(
            username='crmadmin',
            defaults={
                'first_name': 'CRM',
                'last_name': 'Admin',
                'email': 'crmadmin@ralfiz.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'  Created admin user: crmadmin / admin123'))
        else:
            self.stdout.write(f'  Admin user already exists: crmadmin')

        # Create intern users
        interns_data = [
            {'username': 'intern_digital1', 'first_name': 'Arjun', 'last_name': 'Nair', 'type': 'digital'},
            {'username': 'intern_digital2', 'first_name': 'Sneha', 'last_name': 'Menon', 'type': 'digital'},
            {'username': 'intern_field1', 'first_name': 'Rahul', 'last_name': 'Kumar', 'type': 'field'},
            {'username': 'intern_field2', 'first_name': 'Priya', 'last_name': 'Sharma', 'type': 'field'},
        ]

        intern_users = []
        for data in interns_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': f"{data['username']}@ralfiz.com",
                }
            )
            if created:
                user.set_password('intern123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  Created user: {data['username']}"))

            profile, p_created = InternProfile.objects.get_or_create(
                user=user,
                defaults={
                    'intern_type': data['type'],
                    'supervisor': admin,
                    'default_commission_percentage': 5.00,
                    'status': 'active',
                    'joining_date': timezone.now().date() - timedelta(days=random.randint(10, 60)),
                }
            )
            if p_created:
                self.stdout.write(self.style.SUCCESS(f"  Created intern profile: {user.get_full_name()} ({data['type']})"))

            intern_users.append(user)

        # Create sample leads
        leads_data = [
            {'contact_person': 'Mohammed Ali', 'company_name': 'Tech Solutions Kerala', 'phone': '9876543210', 'email': 'ali@techsol.com', 'source': 'instagram', 'status': 'new'},
            {'contact_person': 'Lakshmi Devi', 'company_name': 'Devi Textiles', 'phone': '9876543211', 'email': 'lakshmi@devitex.com', 'source': 'facebook', 'status': 'contacted'},
            {'contact_person': 'Anil George', 'company_name': 'George Motors', 'phone': '9876543212', 'email': 'anil@georgemotors.com', 'source': 'referral', 'status': 'interested'},
            {'contact_person': 'Fatima Begum', 'company_name': 'Begum Catering', 'phone': '9876543213', 'email': 'fatima@begumcatering.com', 'source': 'cold_call', 'status': 'demo_scheduled'},
            {'contact_person': 'Rajesh Pillai', 'company_name': 'Pillai Constructions', 'phone': '9876543214', 'email': 'rajesh@pillaiconst.com', 'source': 'website', 'status': 'follow_up'},
            {'contact_person': 'Suresh Babu', 'company_name': 'Babu Electronics', 'phone': '9876543215', 'email': 'suresh@babuelectro.com', 'source': 'linkedin', 'status': 'converted'},
            {'contact_person': 'Meera Krishnan', 'company_name': 'Krishnan Academy', 'phone': '9876543216', 'email': 'meera@kacademy.com', 'source': 'whatsapp', 'status': 'new'},
            {'contact_person': 'Thomas Varghese', 'company_name': 'Varghese Pharma', 'phone': '9876543217', 'email': 'thomas@vpharma.com', 'source': 'field_visit', 'status': 'interested'},
            {'contact_person': 'Deepa Nambiar', 'company_name': '', 'phone': '9876543218', 'email': 'deepa.n@gmail.com', 'source': 'instagram', 'status': 'lost'},
            {'contact_person': 'Vijay Mohan', 'company_name': 'Mohan Traders', 'phone': '9876543219', 'email': 'vijay@mohantraders.com', 'source': 'referral', 'status': 'contacted'},
        ]

        created_leads = []
        for i, data in enumerate(leads_data):
            lead, created = Lead.objects.get_or_create(
                phone=data['phone'],
                defaults={
                    'contact_person': data['contact_person'],
                    'company_name': data['company_name'],
                    'email': data['email'],
                    'source': data['source'],
                    'status': data['status'],
                    'assigned_to': intern_users[i % len(intern_users)],
                    'closing_probability': random.randint(10, 90),
                    'notes': f"Sample lead for {data['company_name'] or data['contact_person']}",
                    'created_by': admin,
                }
            )
            created_leads.append(lead)
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created lead: {data['contact_person']}"))

        # Create lead notes
        note_texts = [
            'Initial contact made via phone.',
            'Interested in our software solutions.',
            'Requested a demo next week.',
            'Follow-up call scheduled.',
            'Waiting for budget approval from management.',
        ]
        notes_created = 0
        for lead in created_leads[:5]:
            for text in random.sample(note_texts, 2):
                _, created = LeadNote.objects.get_or_create(
                    lead=lead,
                    note=text,
                    defaults={'created_by': admin}
                )
                if created:
                    notes_created += 1
        self.stdout.write(self.style.SUCCESS(f'  Created {notes_created} lead notes'))

        # Create daily activities
        today = timezone.now().date()
        activities_created = 0
        for user in intern_users:
            intern_type = user.intern_profile.intern_type
            for days_ago in range(7):
                date = today - timedelta(days=days_ago)
                _, created = DailyActivity.objects.get_or_create(
                    intern=user,
                    date=date,
                    defaults={
                        'intern_type': intern_type,
                        'social_media_posts': random.randint(0, 5) if intern_type == 'digital' else 0,
                        'reels_created': random.randint(0, 3) if intern_type == 'digital' else 0,
                        'dms_sent': random.randint(0, 20) if intern_type == 'digital' else 0,
                        'digital_leads_generated': random.randint(0, 3) if intern_type == 'digital' else 0,
                        'calls_made': random.randint(0, 15) if intern_type == 'field' else 0,
                        'visits_done': random.randint(0, 5) if intern_type == 'field' else 0,
                        'demos_conducted': random.randint(0, 2) if intern_type == 'field' else 0,
                        'field_leads_generated': random.randint(0, 3) if intern_type == 'field' else 0,
                        'remarks': 'Auto-generated sample data',
                        'approval_status': random.choice(['pending', 'approved', 'approved']),
                        'approved_by': admin if random.random() > 0.3 else None,
                    }
                )
                if created:
                    activities_created += 1
        self.stdout.write(self.style.SUCCESS(f'  Created {activities_created} daily activities'))

        # Create demos
        demos_created = 0
        demo_statuses = ['scheduled', 'completed', 'rescheduled', 'cancelled', 'converted']
        for i, lead in enumerate(created_leads[:6]):
            demo, created = Demo.objects.get_or_create(
                lead=lead,
                defaults={
                    'scheduled_date': timezone.now() + timedelta(days=random.randint(-5, 10)),
                    'status': demo_statuses[i % len(demo_statuses)],
                    'conducted_by': intern_users[i % len(intern_users)],
                    'closing_probability': random.randint(20, 80),
                    'outcome_notes': f'Demo for {lead.contact_person}',
                    'location': random.choice(['Office', 'Client Site', 'Online - Google Meet', 'Online - Zoom']),
                    'created_by': admin,
                }
            )
            if created:
                demos_created += 1
        self.stdout.write(self.style.SUCCESS(f'  Created {demos_created} demos'))

        self.stdout.write(self.style.SUCCESS('\nSample CRM data creation complete!'))
        self.stdout.write(f'\nLogin credentials:')
        self.stdout.write(f'  Admin: crmadmin / admin123')
        self.stdout.write(f'  Interns: intern_digital1, intern_digital2, intern_field1, intern_field2 / intern123')
