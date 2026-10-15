from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import CompanyProfile, Complaint

class StaticViewSitemap(Sitemap):
    """Sitemap para páginas estáticas institucionais da plataforma."""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'core:home',
            'core:search_companies',
            'core:safety_tips',
            'core:news',
            'core:support',
            'core:login',
            'core:signup',
        ]

    def location(self, item):
        return reverse(item)


class CompanyProfileSitemap(Sitemap):
    """Sitemap dinâmico para perfis de empresas cadastradas."""
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        return CompanyProfile.objects.all().order_by('name')

    def lastmod(self, obj):
        return None  # Retorna None ou data da última alteração se houver


class ComplaintSitemap(Sitemap):
    """Sitemap dinâmico para casos e mediações públicas de reclamações."""
    priority = 0.7
    changefreq = 'daily'

    def items(self):
        return Complaint.objects.filter(is_suspended=False).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at
