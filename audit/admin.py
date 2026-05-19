from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'target_model',
                    'target_id', 'ip_address', 'timestamp')
    list_filter = ('action', 'target_model')
    search_fields = ('admin__user__username', 'description')
    readonly_fields = ('admin', 'action', 'target_model',
                       'target_id', 'description', 'ip_address', 'timestamp')

    def has_add_permission(self, request):
        return False  # السجلات تُضاف تلقائياً فقط

    def has_delete_permission(self, request, obj=None):
        return False  # لا يمكن حذف السجلات