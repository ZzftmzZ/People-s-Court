import json
import re
from django.utils import timezone
from .models import ConsumerProfile, Complaint, Message, SupportTicket, AuditLog, CompanyProfile
from .security import encrypt_sensitive_data, decrypt_sensitive_data

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
