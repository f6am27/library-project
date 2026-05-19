from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        # للإداريين
        ('new_reservation', _('New reservation')),
        ('overdue_loan', _('Overdue loan')),
        ('new_review', _('New review pending approval')),
        ('new_member', _('New member registered')),
        # للمنتسبين
        ('loan_due_soon', _('Loan due soon')),
        ('loan_overdue', _('Loan overdue')),
        ('membership_expiring', _('Membership expiring soon')),
        ('reservation_ready', _('Reservation ready for pickup')),
        ('fine_added', _('Fine added')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='notifications',
                             verbose_name=_('user'))
    notification_type = models.CharField(_('type'), max_length=30,
                                         choices=TYPE_CHOICES)
    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))
    is_read = models.BooleanField(_('is read'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    # ربط الإشعار بالعنصر المرتبط به (استعارة، حجز، إلخ)
    target_model = models.CharField(_('target model'), max_length=50,
                                    blank=True, null=True)
    target_id = models.PositiveIntegerField(_('target ID'),
                                            blank=True, null=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.get_notification_type_display()}"

    @classmethod
    def send(cls, user, notification_type, title, message,
             target_model=None, target_id=None):
        """دالة مساعدة لإنشاء إشعار بسطر واحد من أي مكان في المشروع"""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            target_model=target_model,
            target_id=target_id,
        )