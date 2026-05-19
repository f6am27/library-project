from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from .models import Notification
from accounts.views import admin_required

@admin_required
def notification_list_view(request):
    notifications = Notification.objects.filter(
        user=request.user).order_by('-created_at')
    # تحديد الكل كمقروء عند فتح الصفحة
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
    })


@admin_required
def notification_mark_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(request.META.get('HTTP_REFERER', 'notification_list'))


@admin_required
def notification_unread_count_view(request):
    """API endpoint للـ polling كل 30 ثانية"""
    count = Notification.objects.filter(
        user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@admin_required
def notification_mark_all_read_view(request):
    Notification.objects.filter(
        user=request.user, is_read=False).update(is_read=True)
    return redirect('notification_list')