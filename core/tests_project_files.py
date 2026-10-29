"""Staff-only project files: zips, .jks keystores, builds."""
import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Client, Project, ProjectFile

MEDIA = os.path.realpath(tempfile.mkdtemp())


@override_settings(MEDIA_ROOT=MEDIA)
class ProjectFileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client_user = User.objects.create_user('agc_login', password='pw-12345')
        biz = Client.objects.create(name='AGC', email='agc@example.com', user=self.client_user)
        self.project = Project.objects.create(client=biz, name='AGC App', status='in_progress')
        self.client.force_login(self.admin)

    def upload(self, *files, category='keystore'):
        return self.client.post(reverse('project_file_upload', args=[self.project.pk]),
                                {'files': list(files), 'category': category, 'note': 'alias: upload'})

    def test_upload_list_download_delete(self):
        self.upload(SimpleUploadedFile('release.jks', b'KEYSTORE'), SimpleUploadedFile('src.zip', b'PK..'))
        self.assertEqual(ProjectFile.objects.count(), 2)
        pf = ProjectFile.objects.get(name='release.jks')
        self.assertEqual((pf.category, pf.size, pf.note), ('keystore', 8, 'alias: upload'))

        r = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(r, 'release.jks')
        self.assertContains(r, 'src.zip')

        r = self.client.get(reverse('project_file_download', args=[self.project.pk, pf.pk]))
        self.assertEqual(b''.join(r.streaming_content), b'KEYSTORE')
        self.assertIn('release.jks', r['Content-Disposition'])

        path = pf.file.path
        self.client.post(reverse('project_file_delete', args=[self.project.pk, pf.pk]))
        self.assertFalse(ProjectFile.objects.filter(pk=pf.pk).exists())
        self.assertFalse(os.path.exists(path))

    def test_stored_privately_not_served_from_media(self):
        self.upload(SimpleUploadedFile('release.jks', b'KEYSTORE'))
        pf = ProjectFile.objects.get()
        self.assertTrue(pf.file.path.startswith(os.path.join(MEDIA, 'private')))
        self.client.logout()
        r = self.client.get('/media/private/' + pf.file.name)
        self.assertEqual(r.status_code, 404)

    def test_client_login_cannot_download(self):
        self.upload(SimpleUploadedFile('release.jks', b'KEYSTORE'))
        pf = ProjectFile.objects.get()
        self.client.force_login(self.client_user)
        r = self.client.get(reverse('project_file_download', args=[self.project.pk, pf.pk]))
        self.assertEqual(r.status_code, 302)   # client logins are kept in the portal
        r = self.client.get(reverse('client_portal:portal_project_detail', args=[self.project.pk]))
        self.assertNotContains(r, 'release.jks')

    def test_no_file_is_an_error(self):
        r = self.client.post(reverse('project_file_upload', args=[self.project.pk]), {'category': 'other'})
        self.assertEqual(r.status_code, 302)
        self.assertFalse(ProjectFile.objects.exists())
