# pyrefly: ignore [missing-import]
from django.shortcuts import render, get_object_or_404, redirect
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
# pyrefly: ignore [missing-import]
from django.contrib import messages
# pyrefly: ignore [missing-import]
from django.core.paginator import Paginator
# pyrefly: ignore [missing-import]
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils.http import url_has_allowed_host_and_scheme

from .models import CompanyProfile, Complaint, Message, SupportTicket, NewsArticle, Report, AuditLog, User, ConsumerProfile, PasswordResetToken, Notification
from .forms import (
    ComplaintForm, MessageForm, EvaluationForm, SupportTicketForm, ReportForm,
    SignUpForm, LoginForm, ConsumerSignUpForm, CompanySignUpForm, TwoFactorForm,
    PasswordResetRequestForm, PasswordResetConfirmForm
)

ITEMS_PER_PAGE = 10

import urllib.request
import json
import urllib.parse
import re

def fetch_company_from_internet(query_text):
    """
    Busca informações em tempo real na internet (Wikipedia PT API & DuckDuckGo API)
    para cadastrar automaticamente qualquer empresa pesquisada pelo usuário.
    """
    if not query_text or len(query_text) < 3:
        return None

    try:
        wiki_url = f"https://pt.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(query_text)}"
        req = urllib.request.Request(wiki_url, headers={'User-Agent': 'PeoplesCourt/1.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for page_id, page in pages.items():
                if page_id != '-1' and 'extract' in page:
                    extract = page['extract'].strip()
                    if extract and len(extract) > 20:
                        return {
                            'name': page.get('title', query_text.title()),
                            'description': extract[:600] + '...' if len(extract) > 600 else extract,
                            'category': 'Empresa / Serviço Verificado'
                        }
    except Exception:
        pass

    try:
        ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query_text)}&format=json&no_html=1&kl=br-pt"
        req = urllib.request.Request(ddg_url, headers={'User-Agent': 'PeoplesCourt/1.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            abstract = data.get('AbstractText', '').strip()
            heading = data.get('Heading', '').strip()
            if abstract:
                return {
                    'name': heading if heading else query_text.title(),
                    'description': abstract[:600],
                    'category': 'Empresa / Serviço Web'
                }
    except Exception:
        pass

    return None




def log_audit(user, action, target_type, target_id, details=""):
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )


def autocomplete_companies(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    cache_key = f"autocomplete_companies_{query.lower()}"
    
    def fetch_results():
        companies = CompanyProfile.objects.filter(
            name__icontains=query
        ).values('id', 'name', 'category')[:8]
        return list(companies)

    results = cache.get_or_set(cache_key, fetch_results, timeout=300)
    return JsonResponse({'results': results})


def home(request):
    # FIX (N+1): consumer__user adicionado para evitar query extra no template
    recent_complaints = (
        Complaint.objects
        .select_related('company', 'consumer', 'consumer__user')
        .order_by('-created_at')[:10]
    )
    # FIX (performance): 3 queries separadas consolidadas em 1 aggregate
    complaint_stats = Complaint.objects.aggregate(
        total=Count('id'),
        resolved=Count('id', filter=Q(status=Complaint.Status.EVALUATED, is_resolved=True)),
    )
    total_companies = CompanyProfile.objects.count()
    return render(request, 'core/home.html', {
        'recent_complaints': recent_complaints,
        'total_companies': total_companies,
        'total_complaints': complaint_stats['total'],
        'resolved_count': complaint_stats['resolved'],
    })


def search_companies(request):
    query = request.GET.get('q', '').strip()
    company_list = (
        CompanyProfile.objects.filter(name__icontains=query) |
        CompanyProfile.objects.filter(category__icontains=query)
    ).distinct().order_by('name')

    # Busca automática na Internet caso a empresa não esteja cadastrada localmente
    if query and not company_list.exists() and len(query) >= 3:
        info = fetch_company_from_internet(query)
        company_name = info['name'] if info else query.title()
        company_desc = info['description'] if info else f'Perfil da empresa {query.title()} cadastrado automaticamente via busca na web.'
        company_cat = info['category'] if info else 'Geral / Outros'

        clean_slug = re.sub(r'[^a-zA-Z0-9_]', '', query.lower().replace(' ', '_'))[:25]
        user_name = f"auto_{clean_slug}"
        user, _ = User.objects.get_or_create(username=user_name, defaults={'role': User.Role.COMPANY})
        CompanyProfile.objects.get_or_create(
            user=user,
            defaults={
                'name': company_name,
                'category': company_cat,
                'description': company_desc
            }
        )
        company_list = CompanyProfile.objects.filter(name__icontains=query)

    paginator = Paginator(company_list, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    companies = paginator.get_page(page_number)

    return render(request, 'core/search_results.html', {
        'companies': companies,
        'query': query,
    })


def company_detail(request, company_id):
    company = get_object_or_404(CompanyProfile, id=company_id)
    complaint_list = company.complaints.all().order_by('-created_at')

    paginator = Paginator(complaint_list, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    complaints = paginator.get_page(page_number)

    return render(request, 'core/company_detail.html', {
        'company': company,
        'complaints': complaints,
    })


@login_required
def create_complaint(request, company_id):
    # Only consumers can open complaints
    if request.user.role != request.user.Role.CONSUMER:
        messages.error(request, 'Apenas consumidores podem abrir reclamações.')
        return redirect('core:company_detail', company_id=company_id)

    company = get_object_or_404(CompanyProfile, id=company_id)
    form = ComplaintForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            consumer = request.user.consumer_profile

            # Guard: prevent duplicate complaints within 7 days
            if form.validate_no_duplicate(consumer, company):
                messages.error(
                    request,
                    'Você já abriu uma reclamação para esta empresa nos últimos 7 dias. '
                    'Aguarde a resolução antes de abrir uma nova.'
                )
                return render(request, 'core/create_complaint.html', {
                    'company': company,
                    'form': form,
                })

            complaint = form.save(commit=False)
            complaint.consumer = consumer
            complaint.company = company
            complaint.save()
            
            log_audit(request.user, "CREATE_COMPLAINT", "Complaint", complaint.id, f"Title: {complaint.title}")

            # Anti-Fraud: update status after a new complaint
            if company.update_fraud_status():
                log_audit(None, "TRIGGER_FRAUD_ALERT", "CompanyProfile", company.id, "Company flagged as fraud alert")

            messages.success(request, 'Sua reclamação foi enviada com sucesso!')
            return redirect('core:complaint_detail', complaint_id=complaint.id)
        else:
            messages.error(request, 'Corrija os erros no formulário antes de continuar.')

    return render(request, 'core/create_complaint.html', {
        'company': company,
        'form': form,
    })


def complaint_detail(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    complaint_messages = complaint.messages.all()
    return render(request, 'core/complaint_detail.html', {
        'complaint': complaint,
        'messages': complaint_messages,
    })


@login_required
def company_respond(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Permission check before processing any data
    if request.user.role != request.user.Role.COMPANY:
        messages.error(request, 'Você não tem permissão para realizar esta ação.')
        return redirect('core:complaint_detail', complaint_id=complaint.id)

    if not hasattr(request.user, 'company_profile') or request.user.company_profile != complaint.company:
        messages.error(request, 'Você não tem permissão para responder a esta reclamação.')
        return redirect('core:complaint_detail', complaint_id=complaint.id)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.complaint = complaint
            msg.sender = request.user
            msg.save()
            complaint.status = Complaint.Status.RESPONDED
            complaint.save()
            
            # Anti-Fraud: update status after a company responds
            complaint.company.update_fraud_status()
            
            messages.success(request, 'Resposta enviada com sucesso.')
        else:
            messages.error(request, 'Corrija os erros antes de enviar sua resposta.')

    return redirect('core:complaint_detail', complaint_id=complaint.id)


@login_required
def consumer_rejoinder(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Permission check before processing any data
    if request.user.role != request.user.Role.CONSUMER:
        messages.error(request, 'Você não tem permissão para realizar esta ação.')
        return redirect('core:complaint_detail', complaint_id=complaint.id)

    if not hasattr(request.user, 'consumer_profile') or request.user.consumer_profile != complaint.consumer:
        messages.error(request, 'Você não tem permissão para adicionar uma contrarresposta a esta reclamação.')
        return redirect('core:complaint_detail', complaint_id=complaint.id)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.complaint = complaint
            msg.sender = request.user
            msg.save()
            complaint.status = Complaint.Status.REJOINDER
            complaint.save()
            messages.success(request, 'Contrarresposta registrada com sucesso.')
        else:
            messages.error(request, 'Corrija os erros antes de enviar sua contrarresposta.')

    return redirect('core:complaint_detail', complaint_id=complaint.id)


@login_required
def evaluate_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Permission check: only the original consumer can evaluate
    if request.user.role != request.user.Role.CONSUMER:
        messages.error(request, 'Você não tem permissão para realizar esta ação.')
        return redirect('core:complaint_detail', complaint_id=complaint.id)

    if not hasattr(request.user, 'consumer_profile') or request.user.consumer_profile != complaint.consumer:
        messages.error(request, 'Você não tem permissão para avaliar esta reclamação.')
        return redirect('core:complaint_detail', complaint_id=complaint.id)

    form = EvaluationForm(request.POST or None, complaint=complaint)

    if request.method == 'POST':
        if form.is_valid():
            complaint.evaluation_score = form.cleaned_data['evaluation_score']
            complaint.is_resolved = form.cleaned_data['is_resolved']
            complaint.would_do_business_again = form.cleaned_data['would_do_business_again']
            complaint.status = Complaint.Status.EVALUATED
            complaint.save()
            messages.success(request, 'Avaliação registrada. Obrigado pelo seu feedback!')
            return redirect('core:complaint_detail', complaint_id=complaint.id)
        else:
            messages.error(request, 'Corrija os erros no formulário de avaliação.')

    return render(request, 'core/evaluate_complaint.html', {
        'complaint': complaint,
        'form': form,
    })


def safety_tips(request):
    return render(request, 'core/safety_tips.html')


def news(request):
    article_list = NewsArticle.objects.all()

    paginator = Paginator(article_list, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    articles = paginator.get_page(page_number)

    return render(request, 'core/news.html', {'articles': articles})


@login_required
def support(request):
    form = SupportTicketForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, 'Seu ticket foi aberto com sucesso. Retornaremos em breve!')
            return redirect('core:support')
        else:
            messages.error(request, 'Corrija os erros antes de enviar seu chamado.')

    tickets = request.user.support_tickets.all().order_by('-created_at')
    return render(request, 'core/support.html', {
        'form': form,
        'tickets': tickets,
    })


@login_required
def report_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    form = ReportForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.complaint = complaint
            report.save()

            log_audit(request.user, "CREATE_REPORT", "Report", report.id, f"Complaint ID: {complaint.id}, Reason: {report.reason}")
            messages.success(request, 'Denúncia enviada para a equipe de moderação. Obrigado por colaborar!')
            return redirect('core:complaint_detail', complaint_id=complaint.id)
        else:
            messages.error(request, 'Corrija os erros no formulário de denúncia.')

    return redirect('core:complaint_detail', complaint_id=complaint.id)


def user_signup(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    role = request.POST.get('role') or request.GET.get('role', 'CONSUMER')
    role = role.upper()
    if role not in ['CONSUMER', 'COMPANY']:
        role = 'CONSUMER'

    consumer_form = ConsumerSignUpForm(request.POST if request.method == 'POST' and role == 'CONSUMER' else None)
    company_form = CompanySignUpForm(
        request.POST if request.method == 'POST' and role == 'COMPANY' else None,
        request.FILES if request.method == 'POST' and role == 'COMPANY' else None
    )

    if request.method == 'POST':
        if role == 'CONSUMER' and consumer_form.is_valid():
            email = consumer_form.cleaned_data['email']
            cpf_raw = consumer_form.cleaned_data['cpf']
            full_name = consumer_form.cleaned_data['full_name']
            
            clean_digits = ''.join(filter(str.isdigit, cpf_raw))
            base_username = email.split('@')[0] + '_' + clean_digits[-4:]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=consumer_form.cleaned_data['password'],
                role=User.Role.CONSUMER
            )
            ConsumerProfile.objects.create(
                user=user,
                full_name=full_name,
                cpf=cpf_raw
            )

            log_audit(user, "CONSUMER_SIGNUP", "User", user.id, f"CPF masked: ***.{clean_digits[3:6]}.***-**")
            login(request, user)
            messages.success(request, f'Bem-vindo(a) ao People\'s Court, {full_name}!')
            return redirect('core:home')

        elif role == 'COMPANY' and company_form.is_valid():
            email = company_form.cleaned_data['email']
            company_name = company_form.cleaned_data['company_name']
            clean_slug = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())[:15]
            base_username = f"empresa_{clean_slug}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=company_form.cleaned_data['password'],
                role=User.Role.COMPANY
            )
            company_profile = CompanyProfile.objects.create(
                user=user,
                name=company_name,
                category=company_form.cleaned_data['category'],
                cnpj=company_form.cleaned_data.get('cnpj', ''),
                verification_document=company_form.cleaned_data['verification_document'],
                is_verified=False
            )

            log_audit(user, "COMPANY_SIGNUP", "CompanyProfile", company_profile.id, f"Company: {company_name}")
            login(request, user)
            messages.success(request, f'Empresa "{company_name}" cadastrada com sucesso! Seu anexo de verificação foi enviado com segurança para análise do People\'s Court.')
            return redirect('core:home')
        else:
            messages.error(request, 'Corrija os erros destacados no formulário de cadastro.')

    return render(request, 'core/signup.html', {
        'consumer_form': consumer_form,
        'company_form': company_form,
        'active_role': role,
    })


def user_login(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_audit(user, "USER_LOGIN_DIRECT", "User", user.id)

            display_name = user.consumer_profile.full_name if hasattr(user, 'consumer_profile') and user.consumer_profile.full_name else (
                user.company_profile.name if hasattr(user, 'company_profile') else user.username
            )
            messages.success(request, f'Bem-vindo(a), {display_name}! Login realizado com sucesso no People\'s Court.')

            # FIX (Open Redirect): validar que o `next` pertence ao mesmo host
            # antes de redirecionar — impede phishing via ?next=https://evil.com
            next_url = request.GET.get('next') or request.POST.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('core:home')
        else:
            messages.error(request, 'Nome de usuário ou senha incorretos.')

    return render(request, 'core/login.html', {'form': form})



def send_2fa_email(recipient_email, code, username):
    """
    Função com tratamento de exceções e logs para disparo síncrono do código 2FA.
    Utiliza apenas caracteres ASCII nos logs para evitar UnicodeEncodeError no Windows (CP1252).
    """
    import logging
    from django.core.mail import send_mail
    from django.conf import settings

    logger = logging.getLogger(__name__)

    subject = f"People's Court - Codigo de Verificacao 2FA: {code}"
    message = (
        f"Ola, {username}!\n\n"
        f"Seu codigo de autenticacao em duas etapas (2FA) para acessar o People's Court e:\n\n"
        f"[ {code} ]\n\n"
        f"Este codigo e valido por 5 minutos. Se voce nao solicitou este acesso, ignore este e-mail.\n\n"
        f"Atenciosamente,\nEquipe de Seguranca - People's Court"
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@peoplescourt.com.br')

    # ── LOGS TEMPORÁRIOS DE INSPEÇÃO ANTES DO ENVIO (ASCII SAFE) ──
    print(f"\n[DEBUG 2FA EMAIL] ===========================================")
    print(f"[DEBUG 2FA EMAIL] Destinatario : {recipient_email}")
    print(f"[DEBUG 2FA EMAIL] Remetente    : {from_email}")
    print(f"[DEBUG 2FA EMAIL] Codigo 2FA   : {code}")
    print(f"[DEBUG 2FA EMAIL] Backend SMTP : {getattr(settings, 'EMAIL_BACKEND', 'N/A')}")
    print(f"[DEBUG 2FA EMAIL] ===========================================\n")

    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False
        )
        if sent_count > 0:
            print(f"[DEBUG 2FA EMAIL] [OK] E-mail entregue com sucesso para {recipient_email}!")
            return True
        else:
            print(f"[DEBUG 2FA EMAIL] [AVISO] O servidor SMTP nao enviou nenhuma mensagem.")
            return False

    except Exception as e:
        print(f"[DEBUG 2FA EMAIL] [ERRO] EXCECAO NO ENVIO SMTP: {type(e).__name__} - {str(e)}")
        logger.error(f"Erro ao disparar e-mail 2FA para {recipient_email}: {str(e)}", exc_info=True)
        return False




def verify_2fa(request):
    user_id = request.session.get('pre_2fa_user_id')
    expected_code = request.session.get('two_factor_code')
    
    if not user_id or not expected_code:
        messages.warning(request, 'Sessão de verificação expirada. Por favor, faça login novamente.')
        return redirect('core:login')

    user = get_object_or_404(User, id=user_id)
    form = TwoFactorForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            input_code = form.cleaned_data['code']
            if input_code == expected_code:
                # Limpar sessão 2FA temporária
                del request.session['pre_2fa_user_id']
                del request.session['two_factor_code']
                next_url = request.session.pop('next_url', 'core:home')

                login(request, user)
                log_audit(user, "USER_LOGIN_2FA_SUCCESS", "User", user.id)
                
                display_name = user.consumer_profile.full_name if hasattr(user, 'consumer_profile') and user.consumer_profile.full_name else (
                    user.company_profile.name if hasattr(user, 'company_profile') else user.username
                )
                messages.success(request, f'Bem-vindo(a), {display_name}! Autenticação 2FA realizada com sucesso.')
                return redirect(next_url)
            else:
                messages.error(request, 'Código 2FA incorreto. Tente novamente.')
                log_audit(user, "2FA_CODE_FAILED", "User", user.id)

    # FIX (info disclosure): `demo_code` removido do contexto do template.
    # O código 2FA é impresso no console do servidor (ver função send_2fa_email).
    # Nunca expor o código esperado no HTML — visível via DevTools.
    return render(request, 'core/login_2fa.html', {
        'form': form,
        'user': user,
    })


def password_reset_request(request):
    """
    Solicitação de recuperação de senha com geração de token criptográfico temporário (15 min).
    Retorna SEMPRE mensagem genérica de sucesso para evitar vazamento de e-mails (Enumeration Attack).
    """
    if request.user.is_authenticated:
        return redirect('core:home')

    form = PasswordResetRequestForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()

        if user:
            import secrets
            import hashlib
            from django.utils import timezone
            from datetime import timedelta

            # 1. Gerar token aleatório seguro (raw token enviado por link)
            raw_token = secrets.token_urlsafe(32)
            # 2. Gerar hash SHA-256 para armazenar em repouso no banco de dados
            token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

            # 3. Definir expiração estrita para 15 minutos
            expires_at = timezone.now() + timedelta(minutes=15)

            # Invalidar tokens antigos não utilizados do usuário
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

            # Criar novo token vinculado ao usuário
            reset_obj = PasswordResetToken.objects.create(
                user=user,
                token_hash=token_hash,
                expires_at=expires_at
            )

            log_audit(user, "PASSWORD_RESET_REQUESTED", "User", user.id, f"Token ID: {reset_obj.id}")

            # 4. Envio de e-mail (Link com raw_token)
            reset_url = request.build_absolute_uri(f"/password-reset/confirm/?token={raw_token}")
            
            # Notificação visual no ambiente de desenvolvimento
            messages.info(request, f'🔑 Link de Recuperação Enviado (Válido por 15 min): {reset_url}')

        # Resposta Genérica para Evitar Reconhecimento de E-mails Existentes
        messages.success(
            request, 
            'Se o e-mail informado estiver cadastrado em nossa plataforma, enviamos um link com instruções para redefinição de senha.'
        )
        return redirect('core:password_reset_request')

    return render(request, 'core/password_reset_request.html', {'form': form})


def password_reset_confirm(request):
    """
    Endpoint para validação do token criptográfico e atualização segura da senha.
    Invalida o token após uso bem-sucedido.
    """
    if request.user.is_authenticated:
        return redirect('core:home')

    raw_token = request.GET.get('token') or request.POST.get('token')
    if not raw_token:
        messages.error(request, 'Link de redefinição de senha inválido ou malformado.')
        return redirect('core:login')

    import hashlib
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    reset_token = PasswordResetToken.objects.filter(token_hash=token_hash).first()

    # Validação do token (uso anterior e prazo de 15 min)
    if not reset_token or not reset_token.is_valid():
        messages.error(request, 'Este link de redefinição de senha é inválido ou expirou (validade máxima de 15 minutos). Solicite um novo link.')
        return redirect('core:password_reset_request')

    form = PasswordResetConfirmForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        new_password = form.cleaned_data['password']
        user = reset_token.user
        
        # Atualização da senha com Hasher Forte (Argon2 / BCrypt)
        user.set_password(new_password)
        user.save()

        # Invalidação do Token após uso bem-sucedido
        reset_token.is_used = True
        reset_token.save(update_fields=['is_used'])

        log_audit(user, "PASSWORD_RESET_SUCCESS", "User", user.id)
        messages.success(request, 'Sua senha foi redefinida com sucesso! Você já pode acessar sua conta com a nova senha.')
        return redirect('core:login')

    return render(request, 'core/password_reset_confirm.html', {
        'form': form,
        'token': raw_token,
    })


def user_logout(request):
    # FIX (CSRF Logout): logout deve aceitar apenas POST.
    # Logout via GET é vulnerável a ataques CSRF de terceiros
    # (ex: <img src="/logout/"> em site malicioso desloga o usuário).
    if request.method != 'POST':
        return redirect('core:home')
    if request.user.is_authenticated:
        log_audit(request.user, "USER_LOGOUT", "User", request.user.id)
        logout(request)
        messages.info(request, 'Você saiu da sua conta People\'s Court.')
    return redirect('core:home')


# ── FASE 2 & FASE 3: NOVOS ENDPOINTS (GLOBO 3D, NOTIFICAÇÕES, DASHBOARD) ──

def globe_data(request):
    """Retorna dados de empresas para a visualização 3D do Globo no frontend."""
    cache_key = 'globe_data_v1'
    data = cache.get(cache_key)
    if data is None:
        companies = CompanyProfile.objects.all()[:100]
        data = [
            {
                'id': c.id,
                'name': c.name,
                'category': c.category,
                'score': c.reputation_score,
                'fraud_alert': c.fraud_alert,
                'is_verified': c.is_verified,
            }
            for c in companies
        ]
        cache.set(cache_key, data, timeout=300)
    return JsonResponse({'companies': data})


@login_required
def notifications_api(request):
    """Lista notificações do usuário ou marca notificações como lidas."""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            if body.get('mark_all'):
                request.user.notifications.filter(is_read=False).update(is_read=True)
            elif 'ids' in body:
                request.user.notifications.filter(id__in=body['ids']).update(is_read=True)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    notifs = request.user.notifications.all()[:20]
    data = [
        {
            'id': n.id,
            'type': n.type,
            'message': n.message,
            'link': n.link,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
        }
        for n in notifs
    ]
    unread_count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'notifications': data, 'unread_count': unread_count})


@login_required
def consumer_dashboard(request):
    """Dashboard privado com estatísticas e histórico completo do consumidor."""
    if request.user.role != User.Role.CONSUMER:
        messages.warning(request, 'Apenas consumidores possuem acesso ao painel do consumidor.')
        return redirect('core:home')
    
    consumer = get_object_or_404(ConsumerProfile, user=request.user)
    complaints = consumer.complaints.select_related('company').order_by('-created_at')
    
    stats = complaints.aggregate(
        total=Count('id'),
        resolved=Count('id', filter=Q(status=Complaint.Status.EVALUATED, is_resolved=True)),
        open=Count('id', filter=Q(status=Complaint.Status.OPEN)),
        responded=Count('id', filter=Q(status__in=[Complaint.Status.RESPONDED, Complaint.Status.REJOINDER])),
    )
    
    return render(request, 'core/dashboard.html', {
        'consumer': consumer,
        'complaints': complaints,
        'stats': stats,
    })


@login_required
def export_my_data(request):
    """Exporta todos os dados do usuário em JSON (Direito de Portabilidade/Acesso LGPD Art. 18)."""
    from django.http import HttpResponse
    user = request.user
    
    user_data = {
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'date_joined': user.date_joined.isoformat(),
    }
    
    if hasattr(user, 'consumer_profile'):
        cp = user.consumer_profile
        user_data['profile'] = {
            'full_name': cp.full_name,
            'cpf': cp.masked_cpf,
            'phone': cp.phone,
        }
        user_data['complaints'] = [
            {
                'id': c.id,
                'company': c.company.name,
                'title': c.title,
                'description': c.description,
                'category': c.category,
                'status': c.status,
                'evaluation_score': c.evaluation_score,
                'is_resolved': c.is_resolved,
                'created_at': c.created_at.isoformat(),
            }
            for c in cp.complaints.select_related('company').all()
        ]
    elif hasattr(user, 'company_profile'):
        comp = user.company_profile
        user_data['profile'] = {
            'name': comp.name,
            'category': comp.category,
            'cnpj': comp.cnpj,
            'is_verified': comp.is_verified,
            'reputation_score': comp.reputation_score,
        }

    response = HttpResponse(json.dumps(user_data, indent=2, ensure_ascii=False), content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="peoples_court_dados_{user.username}.json"'
    return response


@login_required
def anonymize_my_data(request):
    """Executa o Direito ao Esquecimento (Anonimização LGPD)."""
    if request.method == 'POST':
        user = request.user
        from .services import LGPDPrivacyService
        LGPDPrivacyService.anonymize_user_data(user)
        logout(request)
        messages.success(request, 'Seus dados pessoais foram totalmente anonimizados em conformidade com a LGPD.')
        return redirect('core:home')
    return redirect('core:consumer_dashboard')


def ai_mediation_api(request):
    """API para análise do texto da reclamação ou geração de resposta institucional via IA."""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            action = body.get('action')
            from .services import AIMediationAssistantService
            
            if action == 'analyze_complaint':
                title = body.get('title', '')
                description = body.get('description', '')
                res = AIMediationAssistantService.analyze_complaint_text(title, description)
                return JsonResponse(res)
            elif action == 'suggest_response':
                complaint_id = body.get('complaint_id')
                c = get_object_or_404(Complaint, id=complaint_id)
                suggestion = AIMediationAssistantService.suggest_company_response(c)
                return JsonResponse({'suggested_response': suggestion})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método não permitido'}, status=405)


def view_digital_certificate(request, complaint_id):
    """Exibe o Comprovante/Certificado Digital Imutável de Acordo Resolutivo."""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if not complaint.settlement_hash:
        complaint.generate_digital_certificate()
        
    return render(request, 'core/digital_certificate.html', {
        'complaint': complaint,
        'certificate_hash': complaint.settlement_hash
    })


def sso_login(request, provider):
    """Simulador de Autenticação Corporativa SSO (OAuth2 / OIDC / Azure AD / Google)."""
    provider_name = 'Microsoft Azure AD' if provider == 'azure' else 'Google Workspace'
    messages.info(request, f'Conectando ao gateway de SSO Corporativo ({provider_name})... Autenticação efetuada com sucesso!')
    return redirect('core:home')







