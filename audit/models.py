from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import Admin


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('approve', _('Approve')),
        ('suspend', _('Suspend')),
    ]

    admin = models.ForeignKey(Admin, on_delete=models.PROTECT,
                              related_name='audit_logs',
                              verbose_name=_('admin'))
    action = models.CharField(_('action'), max_length=15,
                              choices=ACTION_CHOICES)
    target_model = models.CharField(_('target model'), max_length=50)
    target_id = models.PositiveIntegerField(_('target ID'),
                                            blank=True, null=True)
    description = models.TextField(_('description'), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_('IP address'),
                                              blank=True, null=True)
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)

    class Meta:
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.admin} — {self.action} {self.target_model} ({self.timestamp:%Y-%m-%d %H:%M})"

    @classmethod
    def log(cls, admin, action, target_model, target_id=None,
            description=None, ip_address=None):
        """دالة مساعدة لتسجيل عملية بسطر واحد من أي مكان"""
        return cls.objects.create(
            admin=admin,
            action=action,
            target_model=target_model,
            target_id=target_id,
            description=description,
            ip_address=ip_address,
        )