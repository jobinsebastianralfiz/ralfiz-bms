"""Interns and staff can be ticked into a project team from the project form."""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Client, Project, TeamMember
from employees.models import Employee
from employees.portal_views import board_member_for


def make_staff(username, role='intern', email='', department='software', status='active'):
    user = User.objects.create_user(username, email, 'pw-12345', first_name=username.title(),
                                    last_name='K')
    return Employee.objects.create(user=user, employee_id=f'EMP-{username.upper()}', role=role,
                                   status=status, joining_date=date(2026, 1, 1), department=department,
                                   employment_type='intern' if role == 'intern' else 'fulltime')


class ProjectTeamInternTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client.force_login(self.admin)
        client = Client.objects.create(name='Alameriah Demo')
        self.project = Project.objects.create(client=client, name='Training Demo', status='in_progress')
        self.dev = TeamMember.objects.create(name='Adbul Rahim CK', role='developer')
        self.intern = make_staff('meera', email='meera@example.com')
        self.linked = make_staff('arun', role='employee', email='arun@example.com')
        TeamMember.objects.create(name='Arun', email='ARUN@example.com', role='developer')
        make_staff('gone', status='terminated')
        make_staff('owner1', role='owner')

    def edit_form(self):
        return self.client.get(reverse('project_update', args=[self.project.pk]))

    def post_team(self, values):
        return self.client.post(reverse('project_update', args=[self.project.pk]), {
            'client': str(self.project.client_id), 'name': self.project.name,
            'project_type': self.project.project_type, 'status': self.project.status,
            'team_members': values,
        })

    def test_form_lists_interns_without_a_team_member(self):
        r = self.edit_form()
        names = [e.full_name for e in r.context['staff_choices']]
        self.assertEqual(names, ['Meera K'])            # arun matched by email; inactive/owner left out
        self.assertContains(r, f'value="emp:{self.intern.pk}"')
        self.assertContains(r, 'Intern')

    def test_ticking_an_intern_makes_a_team_member_and_adds_them(self):
        r = self.post_team([str(self.dev.pk), f'emp:{self.intern.pk}'])
        self.assertEqual(r.status_code, 302)
        member = TeamMember.objects.get(email='meera@example.com')
        self.assertEqual((member.name, member.employment_type, member.role), ('Meera K', 'intern', 'developer'))
        self.assertIsNone(member.user)                  # never linked: keeps the intern confined to /staff/
        self.assertEqual(set(self.project.team_members.all()), {self.dev, member})
        self.assertEqual(board_member_for(self.intern), member)   # staff portal finds their tasks

        # Next time the intern is an ordinary team member, not offered again, and not duplicated.
        self.assertEqual(self.edit_form().context['staff_choices'], [])
        self.post_team([f'emp:{self.intern.pk}'])
        self.assertEqual(TeamMember.objects.filter(email='meera@example.com').count(), 1)

    def test_inactive_match_is_reactivated_not_duplicated(self):
        old = TeamMember.objects.create(name='Meera K', email='meera@example.com', is_active=False)
        self.post_team([f'emp:{self.intern.pk}'])
        old.refresh_from_db()
        self.assertTrue(old.is_active)
        self.assertEqual(list(self.project.team_members.all()), [old])

    def test_bad_values_are_ignored(self):
        self.post_team(['emp:not-a-uuid', 'junk', str(self.dev.pk)])
        self.assertEqual(list(self.project.team_members.all()), [self.dev])
