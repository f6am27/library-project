from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import AuditLog
from accounts.views import admin_required


@admin_required
def audit_log_list_view(request):
    query = request.GET.get('q', '')
    action = request.GET.get('action', '')
    logs = AuditLog.objects.select_related('admin__user').order_by('-timestamp')

    if query:
        logs = logs.filter(
            Q(admin__user__username__icontains=query) |
            Q(target_model__icontains=query) |
            Q(description__icontains=query)
        )
    if action:
        logs = logs.filter(action=action)

    return render(request, 'audit/audit_log_list.html', {
        'logs': logs,
        'action': action,
        'query': query,
        'action_choices': AuditLog.ACTION_CHOICES,
    })