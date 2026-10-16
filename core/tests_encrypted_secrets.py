from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from core.fields import PREFIX, decrypt, encrypt
from core.models import Client, Credential, Project, ProjectNote


def raw(table, column, pk):
    with connection.cursor() as cur:
        cur.execute(f'SELECT {column} FROM {table} WHERE id = %s', [pk.hex if connection.vendor == 'sqlite' else str(pk)])
        return cur.fetchone()[0]


class EncryptedFieldTests(TestCase):
    def setUp(self):
        biz = Client.objects.create(name='AGC', email='agc@example.com')
        self.project = Project.objects.create(client=biz, name='AGC Website', status='in_progress')

    def test_password_is_ciphertext_in_db_and_plain_in_python(self):
        cred = Credential.objects.create(project=self.project, credential_type='dev', name='Staging admin',
                                         username='admin', password='S3cret!pass', ssh_key='-----BEGIN KEY-----')
        stored = raw('core_credential', 'password', cred.pk)
        self.assertTrue(stored.startswith(PREFIX))
        self.assertNotIn('S3cret', stored)
        self.assertEqual(Credential.objects.get(pk=cred.pk).password, 'S3cret!pass')
        self.assertEqual(Credential.objects.get(pk=cred.pk).ssh_key, '-----BEGIN KEY-----')

    def test_legacy_plain_text_still_reads(self):
        self.assertEqual(decrypt('old-plain'), 'old-plain')
        self.assertEqual(decrypt(encrypt('x')), 'x')
        self.assertEqual(encrypt(''), '')

    def test_migration_step_encrypts_existing_rows(self):
        import importlib
        from django.apps import apps
        cred = Credential.objects.create(project=self.project, credential_type='other', name='Legacy', password='plain1')
        with connection.cursor() as cur:   # simulate a row written before encryption
            cur.execute('UPDATE core_credential SET password = %s WHERE id = %s',
                        ['plain1', cred.pk.hex if connection.vendor == 'sqlite' else str(cred.pk)])
        mig = importlib.import_module('core.migrations.0053_encrypt_credentials_project_notes')
        mig.encrypt_existing(apps, None)
        self.assertTrue(raw('core_credential', 'password', cred.pk).startswith(PREFIX))
        self.assertEqual(Credential.objects.get(pk=cred.pk).password, 'plain1')


class ProjectNoteTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client_user = User.objects.create_user('agc_login', password='pw-12345')
        biz = Client.objects.create(name='AGC', email='agc@example.com', user=self.client_user)
        self.project = Project.objects.create(client=biz, name='AGC Website', status='in_progress')
        self.client.force_login(self.admin)

    def test_add_edit_delete_and_encrypted(self):
        url = reverse('project_note_save', args=[self.project.pk])
        self.client.post(url, {'title': 'Staging login', 'body': 'User: admin\nPassword: hunter2', 'pinned': '1'})
        note = ProjectNote.objects.get()
        self.assertTrue(note.pinned)
        self.assertNotIn('hunter2', raw('core_projectnote', 'body', note.pk))
        r = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(r, 'Password: hunter2')
        self.client.post(url, {'note_id': note.pk, 'title': 'Staging login (new)', 'body': 'rotated'})
        note.refresh_from_db()
        self.assertEqual((note.title, note.body, note.pinned), ('Staging login (new)', 'rotated', False))
        self.client.post(reverse('project_note_delete', args=[self.project.pk, note.pk]))
        self.assertFalse(ProjectNote.objects.exists())

    def test_notes_never_reach_the_client_portal(self):
        ProjectNote.objects.create(project=self.project, title='Internal', body='Password: hunter2')
        self.client.force_login(self.client_user)
        r = self.client.get(reverse('client_portal:portal_project_detail', args=[self.project.pk]))
        self.assertNotContains(r, 'hunter2')
        r = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertEqual(r.status_code, 302)   # client logins are kept in the portal

    def test_temporary_flag_saved(self):
        self.client.post(reverse('credential_create'), {
            'project': self.project.pk, 'name': 'Dev DB', 'credential_type': 'dev',
            'username': 'dev', 'password': 'pw', 'is_temporary': 'on'})
        self.assertTrue(Credential.objects.get(name='Dev DB').is_temporary)
