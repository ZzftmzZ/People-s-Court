from django.test import TestCase
from django.urls import reverse
from core.models import User, ConsumerProfile, CompanyProfile
from core.forms import ConsumerSignUpForm, CompanySignUpForm

CPF = '529.982.247-25'
CNPJ = '11.222.333/0001-81'


def consumer_data(**kw):
    d = dict(full_name='Maria Silva', username='maria', email='maria@x.com', cpf=CPF,
             phone='(11) 99999-9999', password='Senha@123', confirm_password='Senha@123', lgpd_consent='on')
    d.update(kw)
    return d


class CadastroTests(TestCase):
    def test_duplicate_email_and_cpf_blocked(self):
        r = self.client.post(reverse('core:signup'), {'role': 'CONSUMER', **consumer_data()})
        self.assertEqual(User.objects.count(), 1, r.content.decode()[:500])
        f = ConsumerSignUpForm(consumer_data(username='outra'))
        self.assertFalse(f.is_valid())
        self.assertIn('email', f.errors)
        self.assertIn('cpf', f.errors)

    def test_duplicate_email_case_insensitive(self):
        self.client.post(reverse('core:signup'), {'role': 'CONSUMER', **consumer_data()})
        f = ConsumerSignUpForm(consumer_data(username='outra', cpf='111.444.777-35', email='MARIA@X.COM'))
        self.assertFalse(f.is_valid())
        self.assertIn('email', f.errors)

    def test_login_by_username_and_email(self):
        self.client.post(reverse('core:signup'), {'role': 'CONSUMER', **consumer_data()})
        self.client.logout()
        for ident in ('maria', 'MARIA@x.com'):
            r = self.client.post(reverse('core:login'), {'username': ident, 'password': 'Senha@123'})
            self.assertEqual(r.status_code, 302, ident)
            self.client.logout()
        r = self.client.post(reverse('core:login'), {'username': 'maria', 'password': 'errada'})
        self.assertEqual(r.status_code, 200)

    def test_company_form_invalid_cnpj_and_category(self):
        f = CompanySignUpForm({'company_name': 'ACME', 'username': 'acme', 'cnpj': '11.111.111/1111-11',
                               'category': 'xxx', 'email': 'a@a.com', 'password': 'Senha@123',
                               'confirm_password': 'Senha@123', 'lgpd_consent': 'on'})
        self.assertFalse(f.is_valid())
        self.assertIn('cnpj', f.errors)
        self.assertIn('category', f.errors)
        self.assertIn('verification_document', f.errors)

    def test_company_page_renders_name_field_and_stays_on_company_tab(self):
        r = self.client.post(reverse('core:signup'), {'role': 'COMPANY', 'company_name': ''})
        html = r.content.decode()
        self.assertIn('id="id_company_name"', html)
        self.assertIn('id="form-company-container" style="display: block;"', html)

    def test_lgpd_page(self):
        self.assertEqual(self.client.get(reverse('core:lgpd_terms')).status_code, 200)

    def test_no_2fa_claim_on_signup(self):
        self.assertNotIn('2FA', self.client.get(reverse('core:signup')).content.decode())

    def test_duplicate_cpf_different_mask(self):
        # Cadastra com máscara padrão 529.982.247-25
        self.client.post(reverse('core:signup'), {'role': 'CONSUMER', **consumer_data()})
        
        # Tenta cadastrar com CPF apenas dígitos (sem máscara)
        raw_digits = ''.join(filter(str.isdigit, CPF))
        f_raw = ConsumerSignUpForm(consumer_data(username='usuario2', email='outro@x.com', cpf=raw_digits))
        self.assertFalse(f_raw.is_valid())
        self.assertIn('cpf', f_raw.errors)

        # Tenta com espaços / formato alternativo
        f_masked = ConsumerSignUpForm(consumer_data(username='usuario3', email='outro2@x.com', cpf=f" {CPF} "))
        self.assertFalse(f_masked.is_valid())
        self.assertIn('cpf', f_masked.errors)

    def test_login_by_email_with_duplicate_legacy_accounts(self):
        # Simula 2 contas antigas criadas previamente com o mesmo e-mail e senhas diferentes
        user1 = User.objects.create_user(username='conta_antiga1', email='legado@x.com', password='SenhaAntiga1@')
        ConsumerProfile.objects.create(user=user1, full_name='Antiga 1', cpf='11122233344')
        
        user2 = User.objects.create_user(username='conta_antiga2', email='legado@x.com', password='SenhaAntiga2@')
        ConsumerProfile.objects.create(user=user2, full_name='Antiga 2', cpf='55566677788')

        # Login com a senha do user2 usando o e-mail compartilhado
        r2 = self.client.post(reverse('core:login'), {'username': 'legado@x.com', 'password': 'SenhaAntiga2@'})
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(str(self.client.session['_auth_user_id']), str(user2.id))
        self.client.logout()

        # Login com a senha do user1 usando o e-mail compartilhado
        r1 = self.client.post(reverse('core:login'), {'username': 'legado@x.com', 'password': 'SenhaAntiga1@'})
        self.assertEqual(r1.status_code, 302)
        self.assertEqual(str(self.client.session['_auth_user_id']), str(user1.id))
        self.client.logout()

    def test_duplicate_cnpj_blocked(self):
        user = User.objects.create_user(username='empresa_antiga', email='empresa1@x.com', password='SenhaForte123@')
        CompanyProfile.objects.create(
            user=user,
            name='Empresa Existente',
            cnpj=CNPJ,
            category='Tecnologia'
        )

        # Tenta cadastrar formulário com o mesmo CNPJ (com máscara)
        f1 = CompanySignUpForm({'company_name': 'Nova Empresa', 'username': 'empresa2', 'cnpj': CNPJ,
                                'category': 'Tecnologia', 'email': 'nova@empresa.com', 'password': 'SenhaForte123@',
                                'confirm_password': 'SenhaForte123@', 'lgpd_consent': 'on'})
        self.assertFalse(f1.is_valid())
        self.assertIn('cnpj', f1.errors)

        # Tenta cadastrar formulário com o mesmo CNPJ (sem máscara)
        raw_cnpj = ''.join(filter(str.isdigit, CNPJ))
        f2 = CompanySignUpForm({'company_name': 'Nova Empresa 2', 'username': 'empresa3', 'cnpj': raw_cnpj,
                                'category': 'Tecnologia', 'email': 'nova2@empresa.com', 'password': 'SenhaForte123@',
                                'confirm_password': 'SenhaForte123@', 'lgpd_consent': 'on'})
        self.assertFalse(f2.is_valid())
        self.assertIn('cnpj', f2.errors)

    def test_complete_platform_flow(self):
        # 1. Cadastro consumidor
        res_signup = self.client.post(reverse('core:signup'), {'role': 'CONSUMER', **consumer_data()})
        self.assertEqual(res_signup.status_code, 302)
        consumer_user = User.objects.get(username='maria')
        self.client.logout()

        # Criação da empresa no sistema
        company_user = User.objects.create_user(username='empresa_flow', email='flow@empresa.com', password='SenhaForte123@', role=User.Role.COMPANY)
        company_profile = CompanyProfile.objects.create(user=company_user, name='Empresa Flow SA', cnpj=CNPJ, category='Tecnologia')

        # 2. Login consumidor por e-mail
        res_login = self.client.post(reverse('core:login'), {'username': 'maria@x.com', 'password': 'Senha@123'})
        self.assertEqual(res_login.status_code, 302)

        # 3. Criar Reclamação
        res_complaint = self.client.post(
            reverse('core:create_complaint', args=[company_profile.id]),
            {'title': 'Problema no serviço contratado', 'description': 'O serviço apresentou falha técnica por 3 dias seguidos.', 'category': 'Serviços'}
        )
        self.assertEqual(res_complaint.status_code, 302)
        from core.models import Complaint
        complaint = Complaint.objects.get(consumer=consumer_user.consumer_profile, company=company_profile)
        self.assertEqual(complaint.status, Complaint.Status.OPEN)
        self.client.logout()

        # 4. Login da Empresa e Envio de Resposta
        self.client.post(reverse('core:login'), {'username': 'empresa_flow', 'password': 'SenhaForte123@'})
        res_resp = self.client.post(
            reverse('core:company_respond', args=[complaint.id]),
            {'content': 'Pedimos desculpas pelo transtorno. O problema foi sanado em nossos servidores.'}
        )
        self.assertEqual(res_resp.status_code, 302)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.RESPONDED)
        self.client.logout()

        # 5. Login consumidor e envio de Réplica
        self.client.post(reverse('core:login'), {'username': 'maria', 'password': 'Senha@123'})
        res_rej = self.client.post(
            reverse('core:consumer_rejoinder', args=[complaint.id]),
            {'content': 'Confirmo que o acesso voltou ao normal. Muito obrigada pelo pronto atendimento.'}
        )
        self.assertEqual(res_rej.status_code, 302)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.REJOINDER)

        # 6. Avaliação final pelo consumidor
        res_eval = self.client.post(
            reverse('core:evaluate_complaint', args=[complaint.id]),
            {'evaluation_score': 10, 'is_resolved': True, 'would_do_business_again': True}
        )
        self.assertEqual(res_eval.status_code, 302)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.EVALUATED)
        self.assertTrue(complaint.is_resolved)

        # 7. Visualização e emissão do Certificado Digital de Acordo
        res_cert = self.client.get(reverse('core:view_digital_certificate', args=[complaint.id]))
        self.assertEqual(res_cert.status_code, 200)
        complaint.refresh_from_db()
        self.assertTrue(bool(complaint.settlement_hash))
        self.assertIn(complaint.settlement_hash, res_cert.content.decode())
