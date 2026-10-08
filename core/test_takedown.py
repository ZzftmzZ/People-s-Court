import uuid
from django.test import TestCase
from django.urls import reverse
from core.forms import ComplaintForm, TakedownRequestForm
from core.models import User, CompanyProfile, ConsumerProfile, Complaint, TakedownRequest, AuditLog
from core.services import TakedownService


class TakedownAndSecurityTests(TestCase):
    def setUp(self):
        self.cu = User.objects.create_user('cons', password='Str0ng!Pass#1', role=User.Role.CONSUMER)
        self.consumer = ConsumerProfile.objects.create(user=self.cu, full_name='C', cpf='52998224725')
        self.ku = User.objects.create_user('comp', password='Str0ng!Pass#1', role=User.Role.COMPANY)
        self.company = CompanyProfile.objects.create(user=self.ku, name='Acme', category='Varejo')
        self.complaint = Complaint.objects.create(
            consumer=self.consumer, company=self.company, title='Titulo', description='Descricao longa do caso', category='X')
        self.other = User.objects.create_user('other', password='Str0ng!Pass#1')

    def test_uuid_pks(self):
        for obj in (self.cu, self.consumer, self.company, self.complaint):
            self.assertIsInstance(obj.pk, uuid.UUID)

    def test_takedown_suspends_and_preserves(self):
        req = TakedownService.submit(self.ku, self.complaint, 'DEFAMATION', 'x' * 40)
        self.complaint.refresh_from_db()
        self.assertTrue(self.complaint.is_suspended)
        self.assertEqual(self.complaint.title, 'Titulo')
        self.assertEqual(len(req.content_hash), 64)
        self.assertTrue(AuditLog.objects.filter(action='TAKEDOWN_REQUESTED').exists())

    def test_duplicate_pending_blocked(self):
        TakedownService.submit(self.ku, self.complaint, 'OTHER', 'x' * 40)
        with self.assertRaises(ValueError):
            TakedownService.submit(self.ku, self.complaint, 'OTHER', 'y' * 40)

    def test_reject_restores(self):
        req = TakedownService.submit(self.ku, self.complaint, 'OTHER', 'x' * 40)
        TakedownService.resolve(req, self.cu, upheld=False)
        self.complaint.refresh_from_db()
        self.assertFalse(self.complaint.is_suspended)

    def test_uphold_keeps_suspended(self):
        req = TakedownService.submit(self.ku, self.complaint, 'OTHER', 'x' * 40)
        TakedownService.resolve(req, self.cu, upheld=True)
        self.complaint.refresh_from_db()
        self.assertTrue(self.complaint.is_suspended)

    def test_suspended_hidden_from_public_visible_to_parties(self):
        TakedownService.submit(self.ku, self.complaint, 'OTHER', 'x' * 40)
        url = reverse('core:complaint_detail', args=[self.complaint.id])
        self.assertEqual(self.client.get(url).status_code, 451)
        self.client.force_login(self.cu)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_takedown_requires_login_and_works(self):
        url = reverse('core:request_takedown', args=[self.complaint.id])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.other)
        r = self.client.post(url, {'reason': 'OTHER', 'justification': 'j' * 40})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(TakedownRequest.objects.count(), 1)

    def test_short_justification_rejected(self):
        self.assertFalse(TakedownRequestForm({'reason': 'OTHER', 'justification': 'curto'}).is_valid())

    def test_bleach_strips_html_on_all_text(self):
        f = ComplaintForm({'title': '<script>alert(1)</script>Oi', 'description': '<img src=x onerror=1>' + 'd' * 30, 'category': '<b>c</b>'})
        f.is_valid()
        for k in ('title', 'description', 'category'):
            v = f.cleaned_data.get(k, '')
            self.assertNotIn('<', v)

    def test_invalid_uuid_404(self):
        self.assertEqual(self.client.get('/complaint/123/').status_code, 404)

    def test_argon2_primary_hasher(self):
        self.assertTrue(User.objects.get(username='cons').password.startswith('argon2'))
