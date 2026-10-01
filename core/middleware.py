import time
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache

class EnterpriseSecurityHeadersMiddleware:
    """Middleware corporativo para inclusão de Security Headers (OWASP Top 10 & ISO 27001)."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # CSP permitindo Three.js, ChartJS, Google Fonts e FontAwesome
        csp_directives = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://api.duckduckgo.com https://pt.wikipedia.org; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response['Content-Security-Policy'] = csp_directives
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=()'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response


class AdvancedRateLimitMiddleware:
    """Rate Limiter defensivo contra DDoS, Brute-Force e Scraping malicioso."""
    def __init__(self, get_response):
        self.get_response = get_response
        self.MAX_REQUESTS_PER_MINUTE = 120

    def __call__(self, request):
        # Ignora arquivos estáticos
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
            
        ip = self._get_client_ip(request)
        current_minute = int(time.time() / 60)
        cache_key = f"rate_limit_{ip}_{current_minute}"
        
        request_count = cache.get(cache_key, 0)
        if request_count >= self.MAX_REQUESTS_PER_MINUTE:
            return JsonResponse({
                'error': 'Too Many Requests',
                'message': 'Limite de requisições excedido por motivos de segurança corporativa. Tente novamente em 1 minuto.'
            }, status=429)
            
        cache.set(cache_key, request_count + 1, timeout=60)
        return self.get_response(request)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
