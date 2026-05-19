from celery import shared_task
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def check_loan_due_dates():
    """تشغّل يومياً — تنبّه المنتسبين قبل 3 أيام من انتهاء الاستعارة"""
    from circulation.models import Loan
    from .models import Notification

    today = timezone.now().date()
    reminder_date = today + timezone.timedelta(days=3)

    loans = Loan.objects.filter(
        status='active',
        due_date=reminder_date
    ).select_related('member__user', 'book_copy__book')

    for loan in loans:
        user = loan.member.user
        book_title = loan.book_copy.book.title

        Notification.send(
            user=user,
            notification_type='loan_due_soon',
            title=str(_('Loan Due Soon')),
            message=f'كتاب "{book_title}" موعد إرجاعه بعد 3 أيام.',
            target_model='Loan',
            target_id=loan.id,
        )

        if user.email:
            send_mail(
                subject='تنبيه: موعد إرجاع كتاب',
                message=f'عزيزي {loan.member.full_name}،\n\nكتاب "{book_title}" موعد إرجاعه {loan.due_date}.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=True,
            )


@shared_task
def check_membership_expiry():
    """تشغّل يومياً — تنبّه المنتسبين قبل 7 أيام من انتهاء الاشتراك"""
    from accounts.models import Member
    from .models import Notification

    today = timezone.now().date()
    reminder_date = today + timezone.timedelta(days=7)

    members = Member.objects.filter(
        membership_end=reminder_date,
        status='active'
    ).select_related('user')

    for member in members:
        Notification.send(
            user=member.user,
            notification_type='membership_expiring',
            title=str(_('Membership Expiring Soon')),
            message=f'اشتراكك ينتهي في {member.membership_end}، يرجى التجديد.',
            target_model='Member',
            target_id=member.id,
        )

        if member.user.email:
            send_mail(
                subject='تنبيه: اشتراكك على وشك الانتهاء',
                message=f'عزيزي {member.full_name}،\n\nاشتراكك ينتهي في {member.membership_end}.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[member.user.email],
                fail_silently=True,
            )