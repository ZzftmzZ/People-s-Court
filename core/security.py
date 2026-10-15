import base64
import hashlib
import hmac
import json
from django.conf import settings
from django.utils import timezone

def _get_encryption_key():
    """Gera uma chave AES-256 baseada no SECRET_KEY da aplicação."""
    secret = getattr(settings, 'SECRET_KEY', 'default-secret-key-peoples-court')
    return hashlib.sha256(secret.encode('utf-8')).digest()

def encrypt_sensitive_data(plain_text: str) -> str:
    """Criptografa dados sensíveis para armazenamento seguro em conformidade com LGPD/GDPR."""
    if not plain_text:
        return ""
    key = _get_encryption_key()
    # XOR com keystream SHA256 derivado da chave + IV
    iv = hashlib.sha256(f"{timezone.now().timestamp()}".encode('utf-8')).digest()[:16]
    keystream = hashlib.sha256(key + iv).digest()
    
    encoded_bytes = plain_text.encode('utf-8')
    cipher_bytes = bytearray()
    for i, b in enumerate(encoded_bytes):
        cipher_bytes.append(b ^ keystream[i % len(keystream)])
    
    token = iv + bytes(cipher_bytes)
    mac = hmac.new(key, token, hashlib.sha256).digest()[:16]
    final_payload = base64.b64encode(mac + token).decode('utf-8')
    return f"ENC:{final_payload}"

def decrypt_sensitive_data(encrypted_text: str) -> str:
    """Descriptografa dados sensíveis criptografados."""
    if not encrypted_text or not encrypted_text.startswith("ENC:"):
        return encrypted_text or ""
    try:
        raw_payload = base64.b64decode(encrypted_text[4:])
        mac = raw_payload[:16]
        token = raw_payload[16:]
        key = _get_encryption_key()
        
        expected_mac = hmac.new(key, token, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(mac, expected_mac):
            return "[DADO CORROMPIDO]"
            
        iv = token[:16]
        cipher_bytes = token[16:]
        keystream = hashlib.sha256(key + iv).digest()
        
        plain_bytes = bytearray()
        for i, b in enumerate(cipher_bytes):
            plain_bytes.append(b ^ keystream[i % len(keystream)])
            
        return plain_bytes.decode('utf-8')
    except Exception:
        return encrypted_text

def compute_audit_hash(prev_hash: str, timestamp_str: str, user_id: str, action: str, details: str) -> str:
    """Calcula o hash de integridade imutável encadeado (Blockchain-style)."""
    raw_data = f"{prev_hash}|{timestamp_str}|{user_id}|{action}|{details}"
    return hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

def compute_settlement_digital_certificate(complaint_id, consumer_cpf: str, company_cnpj: str, score: int, date_str: str) -> str:
    """Gera o selo digital imutável de acordo resolutivo para validade jurídica."""
    secret = getattr(settings, 'SECRET_KEY', 'peoples-court-secret')
    payload = f"SETTLEMENT:{complaint_id}:{consumer_cpf}:{company_cnpj}:{score}:{date_str}:{secret}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def sanitize_text(value: str) -> str:
    """Remove qualquer HTML (anti-XSS). Sem double-escape: o template já faz autoescape."""
    import html
    import bleach
    if not isinstance(value, str):
        return value
    return html.unescape(bleach.clean(value, tags=[], attributes={}, strip=True)).strip()


def compute_content_hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode('utf-8')).hexdigest()
