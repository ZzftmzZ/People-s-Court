from django.contrib import admin
from .models import (User, CompanyProfile, ConsumerProfile, Complaint, Message, SupportTicket,
                     NewsArticle, Report, AuditLog, TakedownRequest, Notification)
from .services import TakedownService


@admin.register(TakedownRequest)
class TakedownRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'complaint', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason')
    readonly_fields = ('content_hash', 'integrity_hash', 'created_at', 'reviewed_at', 'reviewed_by')
    actions = ['uphold', 'reject']

    @admin.action(description='Procedente: manter conteúdo suspenso')
    def uphold(self, request, qs):
        for r in qs.filter(status=TakedownRequest.Status.PENDING):
            TakedownService.resolve(r, request.user, upheld=True)

    @admin.action(description='Improcedente: restabelecer conteúdo')
    def reject(self, request, qs):
        for r in qs.filter(status=TakedownRequest.Status.PENDING):
            TakedownService.resolve(r, request.user, upheld=False)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'target_type', 'target_id', 'user')
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


for m in (User, CompanyProfile, ConsumerProfile, Complaint, Message, SupportTicket, NewsArticle, Report, Notification):
    admin.site.register(m)
