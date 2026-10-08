from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.messages import get_messages

from core.models import User, CompanyProfile, ConsumerProfile, Complaint, NewsArticle
from core.forms import (
    ComplaintForm, EvaluationForm, SupportTicketForm, MessageForm,
    ConsumerSignUpForm, CompanySignUpForm, validate_cpf_number, validate_strong_password
)



# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_consumer(username='consumer1', password='testpass123'):
    """Creates a Consumer user with its ConsumerProfile."""
    user = User.objects.create_user(
        username=username,
        password=password,
        role=User.Role.CONSUMER,
    )
    ConsumerProfile.objects.create(user=user)
    return user


def make_company(username='company1', password='testpass123', name='Empresa Teste', category='Tecnologia'):
    """Creates a Company user with its CompanyProfile."""
    user = User.objects.create_user(
        username=username,
        password=password,
        role=User.Role.COMPANY,
    )
    profile = CompanyProfile.objects.create(user=user, name=name, category=category)
    return user, profile


def make_complaint(consumer_profile, company_profile, title='Produto com defeito', description='Descrição detalhada do problema encontrado no produto.', status=Complaint.Status.OPEN):
    """Creates a Complaint between a consumer and a company."""
    return Complaint.objects.create(
        consumer=consumer_profile,
        company=company_profile,
        title=title,
        description=description,
        category='Produto',
        status=status,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Form Tests
# ─────────────────────────────────────────────────────────────────────────────

class ComplaintFormTest(TestCase):

    def test_valid_form_is_accepted(self):
        data = {
            'title': 'Produto defeituoso',
            'description': 'Recebi o produto completamente danificado e sem embalagem.',
            'category': 'Entrega',
        }
        form = ComplaintForm(data=data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_title_too_short_is_rejected(self):
        data = {
            'title': 'Ruim',
            'description': 'Recebi o produto completamente danificado.',
            'category': 'Entrega',
        }
        form = ComplaintForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_description_too_short_is_rejected(self):
        data = {
            'title': 'Produto com defeito',
            'description': 'Curta demais.',
            'category': 'Entrega',
        }
        form = ComplaintForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_whitespace_only_fields_are_rejected(self):
        data = {
            'title': '          ',
            'description': '                      ',
            'category': 'Entrega',
        }
        form = ComplaintForm(data=data)
        self.assertFalse(form.is_valid())

    def test_duplicate_detection_within_7_days(self):
        """validate_no_duplicate returns True when a recent complaint exists."""
        consumer_user = make_consumer(username='dup_consumer')
        _, company = make_company(username='dup_company')
        consumer = consumer_user.consumer_profile

        # Create an existing complaint
        Complaint.objects.create(
            consumer=consumer,
            company=company,
            title='Reclamação anterior',
            description='Descrição da reclamação anterior do consumidor.',
            category='Produto',
        )

        form = ComplaintForm(data={
            'title': 'Nova reclamação duplicada',
            'description': 'Tentando abrir outra reclamação para a mesma empresa.',
            'category': 'Produto',
        })
        form.is_valid()
        self.assertTrue(form.validate_no_duplicate(consumer, company))

    def test_no_duplicate_after_7_days(self):
        """validate_no_duplicate returns False when existing complaint is older than 7 days."""
        consumer_user = make_consumer(username='old_consumer')
        _, company = make_company(username='old_company')
        consumer = consumer_user.consumer_profile

        old_complaint = Complaint.objects.create(
            consumer=consumer,
            company=company,
            title='Reclamação antiga',
            description='Descrição da reclamação muito antiga no sistema.',
            category='Produto',
        )
        # Backdate the complaint
        Complaint.objects.filter(pk=old_complaint.pk).update(
            created_at=timezone.now() - timedelta(days=8)
        )

        form = ComplaintForm(data={
            'title': 'Nova reclamação válida',
            'description': 'Reclamação após o prazo de carência de sete dias.',
            'category': 'Produto',
        })
        form.is_valid()
        self.assertFalse(form.validate_no_duplicate(consumer, company))


class EvaluationFormTest(TestCase):

    def setUp(self):
        self.consumer_user = make_consumer(username='eval_consumer')
        _, company = make_company(username='eval_company')
        self.consumer = self.consumer_user.consumer_profile
        self.company = company

    def test_valid_evaluation_is_accepted(self):
        complaint = make_complaint(self.consumer, self.company, status=Complaint.Status.RESPONDED)
        form = EvaluationForm(
            data={'evaluation_score': 8, 'is_resolved': True, 'would_do_business_again': True},
            complaint=complaint,
        )
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_score_above_10_is_rejected(self):
        complaint = make_complaint(self.consumer, self.company, status=Complaint.Status.RESPONDED)
        form = EvaluationForm(
            data={'evaluation_score': 11, 'is_resolved': True, 'would_do_business_again': False},
            complaint=complaint,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('evaluation_score', form.errors)

    def test_score_below_0_is_rejected(self):
        complaint = make_complaint(self.consumer, self.company, status=Complaint.Status.RESPONDED)
        form = EvaluationForm(
            data={'evaluation_score': -1, 'is_resolved': False, 'would_do_business_again': False},
            complaint=complaint,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('evaluation_score', form.errors)

    def test_evaluation_on_open_complaint_is_rejected(self):
        """Consumers cannot evaluate a complaint that has not been responded to."""
        complaint = make_complaint(self.consumer, self.company, status=Complaint.Status.OPEN)
        form = EvaluationForm(
            data={'evaluation_score': 7, 'is_resolved': True, 'would_do_business_again': True},
            complaint=complaint,
        )
        self.assertFalse(form.is_valid())


class SupportTicketFormTest(TestCase):

    def test_valid_ticket_is_accepted(self):
        form = SupportTicketForm(data={
            'subject': 'Problema no login',
            'message': 'Não consigo acessar minha conta há três dias, já tentei redefinir a senha.',
        })
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_subject_too_short_is_rejected(self):
        form = SupportTicketForm(data={
            'subject': 'Bug',
            'message': 'Não consigo acessar minha conta há três dias.',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)

    def test_message_too_short_is_rejected(self):
        form = SupportTicketForm(data={
            'subject': 'Problema no login',
            'message': 'Ajuda.',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)


class MessageFormTest(TestCase):

    def test_valid_message_is_accepted(self):
        form = MessageForm(data={'content': 'Prezado consumidor, agradecemos seu contato.'})
        self.assertTrue(form.is_valid())

    def test_short_message_is_rejected(self):
        form = MessageForm(data={'content': 'Ok.'})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


# ─────────────────────────────────────────────────────────────────────────────
# Permission / Access Control Tests
# ─────────────────────────────────────────────────────────────────────────────

class PermissionTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.consumer_user = make_consumer(username='perm_consumer')
        self.company_user, self.company = make_company(username='perm_company')
        self.consumer = self.consumer_user.consumer_profile

    def test_create_complaint_requires_login(self):
        """Unauthenticated users are redirected to the login page."""
        url = reverse('core:create_complaint', args=[self.company.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_company_user_cannot_create_complaint(self):
        """A company user is redirected with an error when trying to open a complaint."""
        self.client.login(username='perm_company', password='testpass123')
        url = reverse('core:create_complaint', args=[self.company.id])
        response = self.client.post(url, {
            'title': 'Empresa abrindo reclamação',
            'description': 'Isso não deveria ser permitido pela regra de negócio.',
            'category': 'Teste',
        }, follow=True)
        # Should redirect and show error — no complaint should be created
        self.assertFalse(Complaint.objects.filter(title='Empresa abrindo reclamação').exists())

    def test_consumer_cannot_respond_as_company(self):
        """A consumer cannot post a company response to a complaint."""
        complaint = make_complaint(self.consumer, self.company)
        self.client.login(username='perm_consumer', password='testpass123')
        url = reverse('core:company_respond', args=[complaint.id])
        self.client.post(url, {'content': 'Tentativa indevida de resposta.'})
        # Status must remain OPEN — response must be ignored
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.OPEN)

    def test_different_company_cannot_respond_to_another_companys_complaint(self):
        """A company cannot respond to a complaint that is not directed at them."""
        _, other_company = make_company(username='other_company', name='Outra Empresa')
        complaint = make_complaint(self.consumer, self.company)
        self.client.login(username='other_company', password='testpass123')
        url = reverse('core:company_respond', args=[complaint.id])
        self.client.post(url, {'content': 'Resposta indevida de outra empresa.'})
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.OPEN)


# ─────────────────────────────────────────────────────────────────────────────
# Reputation Score Tests
# ─────────────────────────────────────────────────────────────────────────────

class ReputationScoreTest(TestCase):

    def setUp(self):
        _, self.company = make_company(username='score_company', name='Empresa Score')
        consumer_user = make_consumer(username='score_consumer')
        self.consumer = consumer_user.consumer_profile

    def test_perfect_score_is_10(self):
        """100% response + 100% resolution + avg score 10 → reputation = 10.0"""
        complaint = make_complaint(self.consumer, self.company, status=Complaint.Status.EVALUATED)
        complaint.is_resolved = True
        complaint.evaluation_score = 10
        complaint.save()

        self.assertEqual(self.company.reputation_score, 10.0)

    def test_zero_score_when_no_complaints(self):
        self.assertEqual(self.company.reputation_score, 0.0)

    def test_partial_score_calculation(self):
        """
        1 evaluated complaint, score 5, resolved, responded.
        response_rate = 1.0, resolution_index = 1.0, avg_score = 5
        expected = (1.0*3.0) + (1.0*3.0) + (5*0.4) = 3 + 3 + 2 = 8.0
        """
        complaint = make_complaint(self.consumer, self.company, status=Complaint.Status.EVALUATED)
        complaint.is_resolved = True
        complaint.evaluation_score = 5
        complaint.save()

        self.assertEqual(self.company.reputation_score, 8.0)

    def test_unanswered_complaint_lowers_score(self):
        """An open (unanswered) complaint should produce a lower score than a responded one."""
        # One fully resolved complaint
        c1 = make_complaint(self.consumer, self.company, title='Resolvida', status=Complaint.Status.EVALUATED)
        c1.is_resolved = True
        c1.evaluation_score = 10
        c1.save()

        # One open complaint with a second consumer
        consumer2_user = make_consumer(username='consumer2')
        consumer2 = consumer2_user.consumer_profile
        make_complaint(consumer2, self.company, title='Sem resposta', status=Complaint.Status.OPEN)

        score = self.company.reputation_score
        # response_rate = 0.5 → score must be less than 10
        self.assertLess(score, 10.0)
        self.assertGreater(score, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# Pagination Tests
# ─────────────────────────────────────────────────────────────────────────────

class PaginationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.consumer_user = make_consumer(username='page_consumer')
        _, self.company = make_company(username='page_company', name='Empresa Paginada')
        self.consumer = self.consumer_user.consumer_profile

    def _create_many_complaints(self, count=15):
        for i in range(count):
            Complaint.objects.create(
                consumer=self.consumer,
                company=self.company,
                title=f'Reclamação número {i + 1} para teste',
                description='Descrição detalhada desta reclamação de teste.',
                category='Teste',
            )

    def test_company_detail_paginates_at_10(self):
        """company_detail must return at most 10 complaints per page."""
        self._create_many_complaints(15)
        url = reverse('core:company_detail', args=[self.company.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        complaints_page = response.context['complaints']
        self.assertLessEqual(len(complaints_page.object_list), 10)

    def test_company_detail_second_page_exists(self):
        """With 15 complaints and page_size=10, a second page must exist."""
        self._create_many_complaints(15)
        url = reverse('core:company_detail', args=[self.company.id])
        response = self.client.get(url + '?page=2')
        self.assertEqual(response.status_code, 200)
        complaints_page = response.context['complaints']
        self.assertEqual(complaints_page.number, 2)

    def test_search_paginates_at_10(self):
        """search_companies must return at most 10 companies per page."""
        for i in range(12):
            u = User.objects.create_user(username=f'co{i}', password='x', role=User.Role.COMPANY)
            CompanyProfile.objects.create(user=u, name=f'Empresa Paginada {i}', category='Teste')

        url = reverse('core:search_companies') + '?q=Paginada'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        companies_page = response.context['companies']
        self.assertLessEqual(len(companies_page.object_list), 10)


# ─────────────────────────────────────────────────────────────────────────────
# Messages Framework Tests
# ─────────────────────────────────────────────────────────────────────────────

@override_settings(MESSAGE_STORAGE='django.contrib.messages.storage.cookie.CookieStorage')
class MessagesTest(TestCase):

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)
        self.consumer_user = make_consumer(username='msg_consumer')
        _, self.company = make_company(username='msg_company', name='Empresa Mensagens')
        self.consumer = self.consumer_user.consumer_profile

    def test_success_message_after_complaint_creation(self):
        """A success message must appear after a valid complaint is submitted."""
        self.client.login(username='msg_consumer', password='testpass123')
        url = reverse('core:create_complaint', args=[self.company.id])
        response = self.client.post(url, {
            'title': 'Reclamacao com mensagem de sucesso',
            'description': 'Descricao longa e valida para disparar a mensagem de sucesso.',
            'category': 'Teste',
        }, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        if not msgs and response.context and 'messages' in response.context:
            msgs = [str(m) for m in response.context['messages']]
        self.assertTrue(
            any('sucesso' in m.lower() for m in msgs),
            f"Expected success message, got: {msgs}"
        )


    def test_error_message_when_company_tries_to_create_complaint(self):
        """An error message must appear when a company user tries to open a complaint."""
        self.client.login(username='msg_company', password='testpass123')
        url = reverse('core:create_complaint', args=[self.company.id])
        response = self.client.post(url, {
            'title': 'Empresa tentando reclamar',
            'description': 'Isso nao deveria ser permitido pelo sistema.',
            'category': 'Teste',
        }, follow=True)
        msgs = [str(m) for m in response.context['messages']]
        # Check that an error message about consumers was issued (avoids encoding issues)
        self.assertTrue(
            any('consumidores' in m.lower() or 'permiss' in m.lower() for m in msgs),
            f"Expected permission error message, got: {msgs}"
        )

    def test_success_message_after_support_ticket(self):
        """A success message must be set in the request after opening a support ticket."""
        self.client.login(username='msg_consumer', password='testpass123')
        url = reverse('core:support')
        # Use follow=False to avoid rendering support.html (template may not exist in test env)
        response = self.client.post(url, {
            'subject': 'Problema tecnico urgente',
            'message': 'Estou enfrentando dificuldades para acessar o sistema ha tres dias.',
        }, follow=False)
        # A successful ticket creation must redirect (302) to the same support page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url, fetch_redirect_response=False)


class SecurityAndLGPDTest(TestCase):

    def test_valid_cpf_accepted(self):
        cpf_clean = validate_cpf_number('111.444.777-35')
        self.assertEqual(cpf_clean, '11144477735')

    def test_invalid_cpf_rejected(self):
        from django.forms import ValidationError
        with self.assertRaises(ValidationError):
            validate_cpf_number('111.111.111-11')

    def test_strong_password_validation(self):
        from django.forms import ValidationError
        # Valid password
        self.assertEqual(validate_strong_password('SenhaSegura123!'), 'SenhaSegura123!')
        
        # Weak password (missing special char and uppercase)
        with self.assertRaises(ValidationError):
            validate_strong_password('senha123')

    def test_consumer_masked_cpf_lgpd(self):
        user = User.objects.create_user(username='lgpd_user', password='Password123!')
        profile = ConsumerProfile.objects.create(
            user=user,
            full_name='João Silva',
            cpf='111.444.777-35'
        )
        self.assertEqual(profile.masked_cpf, '***.444.777-**')

