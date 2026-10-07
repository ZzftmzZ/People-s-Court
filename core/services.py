import json
import re
from django.utils import timezone
from django.db import transaction
from .models import ConsumerProfile, Complaint, Message, SupportTicket, AuditLog, CompanyProfile, TakedownRequest
from .security import encrypt_sensitive_data, decrypt_sensitive_data, compute_audit_hash, compute_content_hash

class AIMediationAssistantService:
    """Serviço de Inteligência Artificial para Auxílio na Mediação Consumidor ↔ Empresa."""
    
    TOXIC_TERMS = ['golpistas', 'bandidos', 'ladrões', 'processar todos', 'safados', 'pilantras', 'fraudadores']
    
    @classmethod
    def analyze_complaint_text(cls, title: str, description: str) -> dict:
        """Analisa o texto do consumidor e sugere aprimoramentos para maior clareza e objetividade sem calúnia/difamação."""
        full_text = f"{title} {description}".lower()
        found_toxic = [term for term in cls.TOXIC_TERMS if term in full_text]
        
        score_clarity = 100
        suggestions = []
        
        if found_toxic:
            score_clarity -= 30
            suggestions.append(
                f"Substitua termos agressivos como '{', '.join(found_toxic)}' por descrições objetivas do fato para evitar rejeição ou denúncia LGPD/difamação."
            )
            
        if len(description.strip()) < 40:
            score_clarity -= 20
            suggestions.append("Detalhe melhor o ocorrido: inclua número de pedido, datas e o impacto enfrentado.")
            
        if "reembolso" not in full_text and "solução" not in full_text and "troca" not in full_text:
            suggestions.append("Especifique claramente qual é o seu objetivo final com a reclamação (ex: reembolso, cancelamento, reparo).")
            
        return {
            'is_objective': len(found_toxic) == 0 and len(description.strip()) >= 40,
            'clarity_score': max(score_clarity, 10),
            'toxic_terms_detected': found_toxic,
            'suggestions': suggestions,
            'ai_refined_hint': "Sua reclamação está objetiva e pronta para mediação corporativa." if not found_toxic else "Recomendamos revisar os termos destacados para aceleração do atendimento."
        }

    @classmethod
    def suggest_company_response(cls, complaint: Complaint) -> str:
        """Gera uma sugestão de resposta institucional empática e orientada a SLA para a empresa."""
        return (
            f"Olá! Lamentamos o inconveniente relatado em relação a '{complaint.title}'. "
            f"Na qualidade de empresa comprometida com a transparência e satisfação dos nossos clientes, "
            f"nossa equipe já registrou o caso sob prioridade. Por gentileza, confirme os detalhes solicitados para que possamos "
            f"efetivar a solução/reembolso de forma ágil e segura."
        )


class AntiFraudEngineService:
    """Motor Heurístico de Prevenção a Fraudes e Detecção de Abusos."""
    
    @classmethod
    def check_duplicate_complaint(cls, consumer: ConsumerProfile, company: CompanyProfile, title: str, description: str) -> bool:
        """Identifica reclamações duplicadas ou spam de um mesmo consumidor em janela curta."""
        recent_cutoff = timezone.now() - timezone.timedelta(days=3)
        existing = Complaint.objects.filter(
            consumer=consumer,
            company=company,
            created_at__gte=recent_cutoff
        )
        
        clean_title = re.sub(r'[^\w\s]', '', title.lower()).strip()
        for c in existing:
            existing_title = re.sub(r'[^\w\s]', '', c.title.lower()).strip()
            if clean_title in existing_title or existing_title in clean_title:
                return True
        return False


class LGPDPrivacyService:
    """Serviço de Conformidade LGPD (Portabilidade de Dados e Direito ao Esquecimento)."""
    
    @classmethod
    def export_user_data(cls, user) -> dict:
        """Exporta todos os dados pessoais do usuário em formato JSON estruturado."""
        data = {
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'date_joined': user.date_joined.isoformat(),
        }
        
        if hasattr(user, 'consumer_profile'):
            cp = user.consumer_profile
            data['consumer_profile'] = {
                'full_name': cp.full_name,
                'cpf_masked': cp.masked_cpf,
                'phone': cp.phone,
            }
            
        complaints = []
        if hasattr(user, 'consumer_profile'):
            for c in user.consumer_profile.complaints.all():
                complaints.append({
                    'id': c.id,
                    'company': c.company.name,
                    'title': c.title,
                    'description': c.description,
                    'status': c.status,
                    'created_at': c.created_at.isoformat(),
                    'evaluation_score': c.evaluation_score,
                    'is_resolved': c.is_resolved
                })
        data['complaints'] = complaints
        return data

    @classmethod
    def anonymize_user_data(cls, user) -> bool:
        """Anonimiza os dados pessoais do usuário (Direito ao Esquecimento) mantendo integridade estatística."""
        if hasattr(user, 'consumer_profile'):
            cp = user.consumer_profile
            cp.full_name = f"Usuário Anonimizado LGPD #{user.id}"
            cp.cpf = "000.000.000-00"
            cp.phone = "(00) 00000-0000"
            cp.save()
            
        user.email = f"anonymized_{user.id}@lgpd.peoplescourt.internal"
        user.first_name = "Anonimizado"
        user.last_name = "LGPD"
        user.is_active = False
        user.save()
        
        AuditLog.objects.create(
            user=None,
            action="LGPD_ANONYMIZATION",
            target_type="User",
            target_id=user.id,
            details=f"Executado Direito ao Esquecimento LGPD para usuário ID #{user.id}"
        )
        return True



def write_chained_audit(user, action, target_type, target_id, details=""):
    """Audit log encadeado: cada hash inclui o hash do registro anterior (imutabilidade verificável)."""
    prev = AuditLog.objects.order_by('-timestamp').values_list('integrity_hash', flat=True).first() or ''
    ts = timezone.now()
    h = compute_audit_hash(prev, ts.isoformat(), str(user.id) if user else 'SYSTEM', action, details)
    return AuditLog.objects.create(
        user=user, action=action, target_type=target_type, target_id=str(target_id),
        details=details, integrity_hash=h,
    )


class TakedownService:
    """Notice and Takedown (Art. 19 Marco Civil): suspende preventivamente, preserva conteúdo e hash."""

    @classmethod
    @transaction.atomic
    def submit(cls, user, complaint, reason, justification):
        if TakedownRequest.objects.filter(
            complaint=complaint, requester=user, status=TakedownRequest.Status.PENDING
        ).exists():
            raise ValueError('Já existe um pedido pendente seu para esta reclamação.')
        content_hash = compute_content_hash(str(complaint.id), complaint.title, complaint.description)
        req = TakedownRequest.objects.create(
            complaint=complaint, requester=user, reason=reason,
            justification=justification, content_hash=content_hash,
        )
        req.integrity_hash = compute_content_hash(str(req.id), content_hash, reason, justification, req.created_at.isoformat())
        req.save(update_fields=['integrity_hash'])
        complaint.is_suspended = True
        complaint.suspended_at = timezone.now()
        complaint.content_hash = content_hash
        complaint.save(update_fields=['is_suspended', 'suspended_at', 'content_hash'])
        write_chained_audit(user, 'TAKEDOWN_REQUESTED', 'Complaint', complaint.id, f'Request {req.id} reason={reason}')
        return req

    @classmethod
    @transaction.atomic
    def resolve(cls, req, reviewer, upheld: bool):
        req.status = TakedownRequest.Status.UPHELD if upheld else TakedownRequest.Status.REJECTED
        req.reviewed_at = timezone.now()
        req.reviewed_by = reviewer
        req.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
        complaint = req.complaint
        if not upheld and not complaint.takedown_requests.filter(status=TakedownRequest.Status.PENDING).exists():
            complaint.is_suspended = False
            complaint.save(update_fields=['is_suspended'])
        write_chained_audit(reviewer, 'TAKEDOWN_RESOLVED', 'Complaint', complaint.id, f'Request {req.id} upheld={upheld}')
        return req
