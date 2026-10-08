import os
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator

def company_document_upload_path(instance, filename):
    """Gera um caminho seguro e renomeia o arquivo enviado com UUID4 para evitar execução maliciosa."""
    ext = filename.split('.')[-1].lower() if '.' in filename else 'pdf'
    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('company_documents', safe_filename)


class User(AbstractUser):
    class Role(models.TextChoices):
        CONSUMER = 'CONSUMER', 'Consumer'
        COMPANY = 'COMPANY', 'Company'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CONSUMER)

class CompanyProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    cnpj = models.CharField(max_length=20, blank=True)
    
    verification_document = models.FileField(
        upload_to=company_document_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg'])],
        help_text="Documento de comprovação da empresa (PDF/PNG/JPG)"
    )
    is_verified = models.BooleanField(default=False, help_text="Status de verificação e autenticidade da empresa")
    
    risk_score = models.FloatField(default=0.0, db_index=True)
    fraud_alert = models.BooleanField(default=False, db_index=True)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('core:company_detail', args=[self.id])
    
    @property
    def reputation_score(self):
        complaints = self.complaints.all()
        total_complaints = complaints.count()
        if total_complaints == 0:
            return 0.0
            
        responded_complaints = complaints.exclude(status=Complaint.Status.OPEN)
        response_rate = responded_complaints.count() / total_complaints
        
        evaluated_complaints = complaints.filter(status=Complaint.Status.EVALUATED)
        total_evaluated = evaluated_complaints.count()
        
        if total_evaluated == 0:
            return round(response_rate * 2.0, 2)  # Base score if no evaluations yet
            
        resolved_complaints = evaluated_complaints.filter(is_resolved=True).count()
        resolution_index = resolved_complaints / total_evaluated
        
        avg_score = evaluated_complaints.aggregate(models.Avg('evaluation_score'))['evaluation_score__avg'] or 0.0
        
        score = (response_rate * 3.0) + (resolution_index * 3.0) + (avg_score * 0.4)
        return round(score, 2)

    @property
    def reputation_badge(self):
        if self.fraud_alert:
            return {'label': 'POSSÍVEL GOLPE', 'color': 'red', 'icon': '⚠️'}
        score = self.reputation_score
        if score >= 8.0:
            return {'label': 'RA1000 (Excelente)', 'color': 'green', 'icon': '💎'}
        elif score >= 7.0:
            return {'label': 'BOM', 'color': 'blue', 'icon': '👍'}
        elif score >= 5.0:
            return {'label': 'REGULAR', 'color': 'yellow', 'icon': '😐'}
        elif score > 0:
            return {'label': 'RUIM', 'color': 'orange', 'icon': '👎'}
        return {'label': 'SEM AVALIAÇÃO', 'color': 'gray', 'icon': '❓'}

    def update_fraud_status(self):
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_complaints = self.complaints.filter(created_at__gte=thirty_days_ago)
        total_recent = recent_complaints.count()
        
        if total_recent > 5:
            responded = recent_complaints.exclude(status=Complaint.Status.OPEN).count()
            response_rate = responded / total_recent
            
            if response_rate < 0.3:
                if not self.fraud_alert:
                    self.fraud_alert = True
                    self.risk_score = 100.0
                    self.save(update_fields=['fraud_alert', 'risk_score'])
                return True
                
        return False

    def __str__(self):
        return self.name

class ConsumerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='consumer_profile')
    full_name = models.CharField(max_length=255, blank=True)
    cpf = models.CharField(max_length=14, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)

    @property
    def masked_cpf(self):
        """Retorna o CPF mascarado para proteção de privacidade de dados em conformidade com a LGPD."""
        clean = ''.join(filter(str.isdigit, self.cpf or ''))
        if len(clean) == 11:
            return f"***.{clean[3:6]}.{clean[6:9]}-**"
        return "***.***.***-**"

    def __str__(self):
        return self.full_name or self.user.username


class Complaint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        RESPONDED = 'RESPONDED', 'Company Responded'
        REJOINDER = 'REJOINDER', 'Consumer Rejoinder'
        EVALUATED = 'EVALUATED', 'Final Evaluation'

    consumer = models.ForeignKey(ConsumerProfile, on_delete=models.CASCADE, related_name='complaints')
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    evidence = models.FileField(
        upload_to='complaint_evidences/%Y/%m/%d/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg'])]
    )
    
    # Final Evaluation fields
    evaluation_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
    is_resolved = models.BooleanField(null=True, blank=True)
    would_do_business_again = models.BooleanField(null=True, blank=True)
    settlement_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True, help_text="Selo Digital Imutável de Acordo Resolutivo")

    # Notice and Takedown (Marco Civil, Art. 19): suspensão preventiva sem apagar o conteúdo
    is_suspended = models.BooleanField(default=False, db_index=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, blank=True, null=True, help_text="SHA-256 do conteúdo no momento da suspensão")

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('core:complaint_detail', args=[self.id])

    def generate_digital_certificate(self):
        from .security import compute_settlement_digital_certificate
        if self.status == self.Status.EVALUATED and self.is_resolved:
            cpf = self.consumer.cpf if self.consumer else "00000000000"
            cnpj = self.company.cnpj if self.company else "00000000000000"
            score = self.evaluation_score or 10
            date_str = self.updated_at.strftime('%Y%m%d%H%M%S')
            cert_hash = compute_settlement_digital_certificate(self.id, cpf, cnpj, score, date_str)
            self.settlement_hash = cert_hash
            self.save(update_fields=['settlement_hash'])
            return cert_hash
        return self.settlement_hash

    def __str__(self):
        return f"{self.title} - {self.company.name}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.username} on {self.complaint.title}"

class SupportTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'
        
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket {self.id} - {self.subject}"

class NewsArticle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    summary = models.TextField()
    source_name = models.CharField(max_length=100)
    external_link = models.URLField()
    publication_date = models.DateTimeField(db_index=True)
    category_tags = models.CharField(max_length=255, help_text="Comma separated tags, e.g., Fraud, Security")
    
    class Meta:
        ordering = ['-publication_date']

    def __str__(self):
        return self.title


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Reason(models.TextChoices):
        OFFENSIVE = 'OFFENSIVE', 'Linguagem Ofensiva / Inapropriada'
        PERSONAL_DATA = 'PERSONAL_DATA', 'Exposição de Dados Pessoais (LGPD)'
        FALSE_FRAUD = 'FALSE_FRAUD', 'Denúncia Falsa / Difamação'
        OTHER = 'OTHER', 'Outros Motivos'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente de Análise'
        APPROVED = 'APPROVED', 'Aprovado (Conteúdo Moderado)'
        REJECTED = 'REJECTED', 'Rejeitado (Improcedente)'

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_submitted')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Report {self.id} on Complaint {self.complaint_id} ({self.status})"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=50, db_index=True)
    target_id = models.CharField(max_length=64, db_index=True)
    details = models.TextField(blank=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    integrity_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.action} by {self.user}"


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Reset Token for {self.user.username} (Used: {self.is_used})"


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Type(models.TextChoices):
        COMPANY_RESPONDED = 'RESPONDED', 'Empresa respondeu'
        FRAUD_ALERT       = 'FRAUD',     'Alerta de fraude'
        CASE_EVALUATED    = 'EVALUATED', 'Caso avaliado'
        SUPPORT_UPDATE    = 'SUPPORT',   'Ticket atualizado'

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=Type.choices)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"





class TakedownRequest(models.Model):
    """Pedido de remoção/contestação (Notice and Takedown, Art. 19 Marco Civil)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Reason(models.TextChoices):
        DEFAMATION = 'DEFAMATION', 'Conteúdo falso / ofensivo à honra'
        PERSONAL_DATA = 'PERSONAL_DATA', 'Exposição de dados pessoais (LGPD)'
        COPYRIGHT = 'COPYRIGHT', 'Violação de direitos autorais'
        OTHER = 'OTHER', 'Outro motivo'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente (conteúdo suspenso preventivamente)'
        UPHELD = 'UPHELD', 'Procedente (conteúdo mantido suspenso)'
        REJECTED = 'REJECTED', 'Improcedente (conteúdo restabelecido)'

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='takedown_requests')
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='takedown_requests')
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    justification = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    content_hash = models.CharField(max_length=64, help_text="SHA-256 do conteúdo contestado")
    integrity_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='takedowns_reviewed')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Takedown {self.id} ({self.status})"
