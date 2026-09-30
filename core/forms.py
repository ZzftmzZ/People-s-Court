# pyrefly: ignore [missing-import]
from django import forms
from django.db import models
import bleach
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth.forms import AuthenticationForm
from .models import Complaint, Message, SupportTicket, Report, User, ConsumerProfile, CompanyProfile


class ComplaintForm(forms.ModelForm):
    """
    Form for creating a new complaint.

    Validates:
    - Minimum length for title (10 chars) and description (20 chars).
    - Strips leading/trailing whitespace from all text fields.
    - Prevents the same consumer from filing a duplicate complaint
      against the same company within the last 7 days.
    """

    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'evidence']
        widgets = {
            'title': forms.TextInput(attrs={
                'id': 'id_complaint_title',
                'placeholder': 'Resumo claro do problema',
                'class': 'w-full',
            }),
            'description': forms.Textarea(attrs={
                'id': 'id_complaint_description',
                'rows': 6,
                'placeholder': 'Descreva o ocorrido com detalhes (mínimo 20 caracteres)',
                'class': 'w-full',
            }),
            'category': forms.TextInput(attrs={
                'id': 'id_complaint_category',
                'placeholder': 'Ex: Cobrança indevida, Entrega, Atendimento…',
                'class': 'w-full',
            }),
            'evidence': forms.FileInput(attrs={
                'id': 'id_complaint_evidence',
                'class': 'w-full text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100'
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        title = bleach.clean(title)
        if len(title) < 10:
            raise forms.ValidationError(
                'O título precisa ter pelo menos 10 caracteres.'
            )
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        description = bleach.clean(description)
        if len(description) < 20:
            raise forms.ValidationError(
                'A descrição precisa ter pelo menos 20 caracteres.'
            )
        return description

    def clean_category(self):
        return self.cleaned_data.get('category', '').strip()

    def validate_no_duplicate(self, consumer, company):
        """
        Call this in the view after form.is_valid() to check for duplicates.
        Returns True if a duplicate exists within the last 7 days.
        """
        one_week_ago = timezone.now() - timedelta(days=7)
        return Complaint.objects.filter(
            consumer=consumer,
            company=company,
            created_at__gte=one_week_ago,
        ).exists()


class MessageForm(forms.ModelForm):
    """
    Form for posting a message (company response or consumer rejoinder).

    Validates:
    - Minimum length of 10 characters.
    - Strips whitespace.
    """

    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'id': 'id_message_content',
                'rows': 4,
                'placeholder': 'Escreva sua mensagem aqui (mínimo 10 caracteres)…',
                'class': 'w-full',
            }),
        }
        labels = {
            'content': 'Mensagem',
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 10:
            raise forms.ValidationError(
                'A mensagem precisa ter pelo menos 10 caracteres.'
            )
        return content


class EvaluationForm(forms.Form):
    """
    Form for the consumer's final evaluation of a complaint resolution.

    Validates:
    - evaluation_score is between 0 and 10.
    - The complaint is in a state that allows evaluation
      (RESPONDED or REJOINDER).
    """

    evaluation_score = forms.IntegerField(
        min_value=0,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'id': 'id_evaluation_score',
            'class': 'w-full',
        }),
        label='Nota (0 a 10)',
        error_messages={
            'min_value': 'A nota mínima é 0.',
            'max_value': 'A nota máxima é 10.',
        },
    )

    is_resolved = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'id_is_resolved'}),
        label='O problema foi resolvido?',
    )

    would_do_business_again = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'id_would_do_business_again'}),
        label='Voltaria a fazer negócio com esta empresa?',
    )

    def __init__(self, *args, complaint=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.complaint = complaint

    def clean(self):
        cleaned_data = super().clean()
        if self.complaint:
            allowed_states = [
                Complaint.Status.RESPONDED,
                Complaint.Status.REJOINDER,
            ]
            if self.complaint.status not in allowed_states:
                raise forms.ValidationError(
                    'Esta reclamação ainda não pode ser avaliada. '
                    'Aguarde a resposta da empresa.'
                )
        return cleaned_data


class SupportTicketForm(forms.ModelForm):
    """
    Form for opening a support ticket.

    Validates:
    - Minimum 5 chars for subject, 20 chars for message.
    - Strips whitespace from both fields.
    """

    class Meta:
        model = SupportTicket
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={
                'id': 'id_ticket_subject',
                'placeholder': 'Assunto do seu chamado',
                'class': 'w-full',
            }),
            'message': forms.Textarea(attrs={
                'id': 'id_ticket_message',
                'rows': 5,
                'placeholder': 'Descreva sua solicitação com detalhes (mínimo 20 caracteres)',
                'class': 'w-full',
            }),
        }

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if len(subject) < 5:
            raise forms.ValidationError(
                'O assunto precisa ter pelo menos 5 caracteres.'
            )
        return subject

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 20:
            raise forms.ValidationError(
                'A mensagem precisa ter pelo menos 20 caracteres.'
            )
        return message


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={
                'id': 'id_report_reason',
                'class': 'w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white',
            }),
            'description': forms.Textarea(attrs={
                'id': 'id_report_description',
                'rows': 3,
                'placeholder': 'Descreva o motivo da denúncia...',
                'class': 'w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white',
            }),
        }


import re

def validate_cpf_number(value):
    """
    Valida formato e dígitos verificadores oficiais do CPF brasileiro (Algoritmo Módulo 11).
    """
    cpf = ''.join(filter(str.isdigit, str(value or '')))
    if len(cpf) != 11:
        raise forms.ValidationError('O CPF deve conter exatamente 11 dígitos numéricos.')
    
    if cpf == cpf[0] * 11:
        raise forms.ValidationError('CPF inválido. Verifique os números digitados.')
    
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito_1 = (soma * 10) % 11
    if digito_1 == 10:
        digito_1 = 0
    if digito_1 != int(cpf[9]):
        raise forms.ValidationError('Dígitos verificadores do CPF inválidos.')
    
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito_2 = (soma * 10) % 11
    if digito_2 == 10:
        digito_2 = 0
    if digito_2 != int(cpf[10]):
        raise forms.ValidationError('Dígitos verificadores do CPF inválidos.')

    return cpf


def validate_strong_password(password):
    """
    Valida regra forte de complexidade de senha:
    - Mínimo de 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    """
    if len(password) < 8:
        raise forms.ValidationError('A senha deve ter no mínimo 8 caracteres.')
    if not re.search(r'[A-Z]', password):
        raise forms.ValidationError('A senha deve conter pelo menos uma letra maiúscula.')
    if not re.search(r'[a-z]', password):
        raise forms.ValidationError('A senha deve conter pelo menos uma letra minúscula.')
    if not re.search(r'[0-9]', password):
        raise forms.ValidationError('A senha deve conter pelo menos um número.')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?\\|/]', password):
        raise forms.ValidationError('A senha deve conter pelo menos um caractere especial (!@#$%...).')
    return password


def validate_secure_document_upload(file):
    """
    Valida o envio seguro de anexos de empresas:
    - Envio obrigatório
    - Extensão permitida (PDF, PNG, JPG, JPEG)
    - Limite de tamanho máximo de 5MB
    - Verificação de cabeçalho mágico (MIME type real)
    """
    if not file:
        raise forms.ValidationError('O envio do documento de comprovação da empresa é obrigatório.')
    
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise forms.ValidationError('O arquivo excede o tamanho máximo de 5MB.')
    
    ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
    if ext not in ['pdf', 'png', 'jpg', 'jpeg']:
        raise forms.ValidationError(f'Extensão .{ext} não permitida. Envie arquivos PDF, PNG ou JPG.')
    
    header = file.read(10)
    file.seek(0)
    
    is_pdf = header.startswith(b'%PDF')
    is_png = header.startswith(b'\x89PNG')
    is_jpg = header.startswith(b'\xff\xd8\xff')
    
    if not (is_pdf or is_png or is_jpg):
        raise forms.ValidationError('O arquivo enviado é inválido ou alterado. Certifique-se de enviar um PDF ou imagem válida.')
    
    return file


class ConsumerSignUpForm(forms.Form):
    """Formulário restrito de cadastro de usuário consumidor conforme LGPD."""
    full_name = forms.CharField(
        label='Nome Completo',
        max_length=255,
        widget=forms.TextInput(attrs={
            'id': 'id_signup_full_name',
            'placeholder': 'Seu nome completo',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    email = forms.EmailField(
        label='Endereço de E-mail',
        widget=forms.EmailInput(attrs={
            'id': 'id_signup_email',
            'placeholder': 'seu@email.com',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        validators=[validate_cpf_number],
        widget=forms.TextInput(attrs={
            'id': 'id_signup_cpf',
            'placeholder': '000.000.000-00',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    password = forms.CharField(
        label='Senha',
        validators=[validate_strong_password],
        widget=forms.PasswordInput(attrs={
            'id': 'id_signup_password',
            'placeholder': 'Senha forte (mín. 8 chars, A-z, 0-9, @#$)',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    confirm_password = forms.CharField(
        label='Confirmação de Senha',
        widget=forms.PasswordInput(attrs={
            'id': 'id_signup_confirm_password',
            'placeholder': 'Repita sua senha',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if len(full_name.split()) < 2:
            raise forms.ValidationError('Por favor, informe seu nome e sobrenome completos.')
        return full_name

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'As senhas digitadas não coincidem.')
        return cleaned_data


class CompanySignUpForm(forms.Form):
    """Formulário de cadastro de empresa com envio obrigatório de anexo de verificação."""
    company_name = forms.CharField(
        label='Nome da Empresa',
        max_length=255,
        widget=forms.TextInput(attrs={
            'id': 'id_company_name',
            'placeholder': 'Razão Social ou Nome Fantasia',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    cnpj = forms.CharField(
        label='CNPJ',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_company_cnpj',
            'placeholder': '00.000.000/0001-00',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    category = forms.CharField(
        label='Categoria',
        max_length=100,
        widget=forms.TextInput(attrs={
            'id': 'id_company_category',
            'placeholder': 'Ex: E-commerce, Financeiro, Serviços',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    email = forms.EmailField(
        label='E-mail Corporativo',
        widget=forms.EmailInput(attrs={
            'id': 'id_company_email',
            'placeholder': 'contato@empresa.com.br',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    verification_document = forms.FileField(
        label='Documento Comprobatório (Obrigatório)',
        validators=[validate_secure_document_upload],
        widget=forms.FileInput(attrs={
            'id': 'id_company_document',
            'accept': '.pdf,.png,.jpg,.jpeg',
            'class': 'w-full text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-800 file:text-white hover:file:bg-gray-700'
        }),
        help_text='Envie um comprovante (Contrato Social, Cartão CNPJ ou documento em PDF/Imagem de até 5MB).'
    )
    password = forms.CharField(
        label='Senha',
        validators=[validate_strong_password],
        widget=forms.PasswordInput(attrs={
            'id': 'id_company_password',
            'placeholder': 'Senha corporativa forte',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )
    confirm_password = forms.CharField(
        label='Confirmação de Senha',
        widget=forms.PasswordInput(attrs={
            'id': 'id_company_confirm_password',
            'placeholder': 'Repita a senha',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'As senhas digitadas não coincidem.')
        return cleaned_data


class SignUpForm(forms.ModelForm):
    """Formulário unificado para retrocompatibilidade."""
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.Select(attrs={
            'id': 'id_signup_role',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white mb-4'
        }),
        initial=User.Role.CONSUMER,
        label='Tipo de Conta'
    )
    full_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_signup_full_name',
            'placeholder': 'Nome Completo',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        }),
        label='Nome Completo'
    )
    cpf = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_signup_cpf',
            'placeholder': 'CPF (000.000.000-00)',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        }),
        label='CPF'
    )
    verification_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'id': 'id_signup_document',
            'class': 'w-full text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-800 file:text-white'
        }),
        label='Documento Comprobatório (Empresas)'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'id_signup_password',
            'placeholder': 'Sua senha forte',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        }),
        label='Senha'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'id_signup_confirm_password',
            'placeholder': 'Confirme sua senha',
            'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
        }),
        label='Confirmação de Senha'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role']
        widgets = {
            'username': forms.TextInput(attrs={
                'id': 'id_signup_username',
                'placeholder': 'Nome de Usuário',
                'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
            }),
            'email': forms.EmailInput(attrs={
                'id': 'id_signup_email',
                'placeholder': 'seu@email.com',
                'class': 'w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-lg text-white'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        role = cleaned_data.get('role')
        cpf = cleaned_data.get('cpf')
        document = cleaned_data.get('verification_document')

        if password:
            validate_strong_password(password)

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'As senhas digitadas não coincidem.')

        if role == User.Role.CONSUMER and cpf:
            validate_cpf_number(cpf)

        if role == User.Role.COMPANY:
            if not document:
                self.add_error('verification_document', 'O envio de anexo comprobatório é obrigatório para o cadastro de empresa.')
            else:
                validate_secure_document_upload(document)

        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Nome de Usuário',
        widget=forms.TextInput(attrs={
            'id': 'id_login_username',
            'placeholder': 'Digite seu nome de usuário',
            'class': 'w-full px-4 py-3 bg-[#000000] border border-[#27272a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-white transition-colors',
            'autofocus': 'autofocus'
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'id': 'id_login_password',
            'placeholder': 'Sua senha de acesso',
            'class': 'w-full px-4 py-3 bg-[#000000] border border-[#27272a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-white transition-colors'
        })
    )



class TwoFactorForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'id': 'id_2fa_code',
            'placeholder': '000000',
            'maxlength': '6',
            'class': 'w-full px-4 py-3 bg-[#000000] border border-[#27272a] rounded-lg text-white font-mono text-center text-2xl tracking-[0.5em] focus:outline-none focus:border-white transition-colors',
            'autocomplete': 'one-time-code',
            'autofocus': 'autofocus'
        }),
        label='Código de Verificação 2FA (6 dígitos)'
    )

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label='E-mail Cadastrado',
        widget=forms.EmailInput(attrs={
            'id': 'id_reset_email',
            'placeholder': 'seu@email.com',
            'class': 'w-full px-4 py-3 bg-[#000000] border border-[#27272a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-white transition-colors'
        })
    )


class PasswordResetConfirmForm(forms.Form):
    password = forms.CharField(
        label='Nova Senha',
        validators=[validate_strong_password],
        widget=forms.PasswordInput(attrs={
            'id': 'id_reset_password',
            'placeholder': 'Nova senha forte (mínimo 8 caracteres)',
            'class': 'w-full px-4 py-3 bg-[#000000] border border-[#27272a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-white transition-colors'
        })
    )
    confirm_password = forms.CharField(
        label='Confirmação da Nova Senha',
        widget=forms.PasswordInput(attrs={
            'id': 'id_reset_confirm_password',
            'placeholder': 'Repita a nova senha',
            'class': 'w-full px-4 py-3 bg-[#000000] border border-[#27272a] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-white transition-colors'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'As senhas digitadas não coincidem.')
        return cleaned_data





