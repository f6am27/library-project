from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    phone = models.CharField(_('phone'), max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.username


class MembershipPlan(models.Model):
    PLAN_TYPES = [
        ('monthly', _('Monthly')),
        ('yearly', _('Yearly')),
    ]

    name = models.CharField(_('name'), max_length=100)
    plan_type = models.CharField(_('plan type'), max_length=10, choices=PLAN_TYPES)
    duration_months = models.PositiveIntegerField(_('duration in months'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    max_loans = models.PositiveIntegerField(_('max loans allowed'), default=1)
    is_active = models.BooleanField(_('is active'), default=True)

    class Meta:
        verbose_name = _('membership plan')
        verbose_name_plural = _('membership plans')

    def __str__(self):
        return f"{self.name} - {self.price}"


class Member(models.Model):
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('suspended', _('Suspended')),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='member_profile', verbose_name=_('user'))
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT,
                             related_name='members', verbose_name=_('membership plan'))
    membership_number = models.CharField(_('membership number'), max_length=20,
                                         unique=True, editable=False)
    full_name = models.CharField(_('full name'), max_length=150)
    national_id = models.CharField(_('national ID'), max_length=20, unique=True)
    id_image = models.ImageField(_('ID image'), upload_to='members/ids/',
                                 blank=True, null=True)
    address = models.TextField(_('address'), blank=True, null=True)
    membership_start = models.DateField(_('membership start'))
    membership_end = models.DateField(_('membership end'))
    status = models.CharField(_('status'), max_length=15,
                              choices=STATUS_CHOICES, default='active')

    class Meta:
        verbose_name = _('member')
        verbose_name_plural = _('members')

    def __str__(self):
        return f"{self.membership_number} - {self.full_name}"

    def save(self, *args, **kwargs):
        # توليد رقم الانتساب تلقائياً عند الإنشاء
        if not self.membership_number:
            last = Member.objects.order_by('id').last()
            next_id = (last.id + 1) if last else 1
            self.membership_number = f"LIB-{next_id:05d}"
        super().save(*args, **kwargs)


class Admin(models.Model):
    ROLE_CHOICES = [
        ('super_admin', _('Super Admin')),
        ('librarian', _('Librarian')),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='admin_profile', verbose_name=_('user'))
    role = models.CharField(_('role'), max_length=15,
                            choices=ROLE_CHOICES, default='librarian')

    class Meta:
        verbose_name = _('admin')
        verbose_name_plural = _('admins')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"