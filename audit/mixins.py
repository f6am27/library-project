from .models import AuditLog


def log_action(request, action, target_model, target_id=None, description=None):
    """استخدميها في أي view تريدين تسجيله"""
    try:
        from accounts.models import Admin
        admin = Admin.objects.get(user=request.user)
        ip = request.META.get('HTTP_X_FORWARDED_FOR',
                              request.META.get('REMOTE_ADDR', ''))
        AuditLog.log(
            admin=admin,
            action=action,
            target_model=target_model,
            target_id=target_id,
            description=description,
            ip_address=ip,
        )
    except Exception:
        pass  # لا نوقف العملية إذا فشل التسجيل