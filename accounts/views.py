from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from .models import User, Member, MembershipPlan, Admin
from .forms import LoginForm, MemberForm, UserCreateForm
from circulation.models import Loan, Fine, BookRequest, DirectSale
from django.db.models import Sum


# ───── دوال مساعدة للصلاحيات ─────

def is_admin(user):
    if not user.is_authenticated:
        return False
    try:
        return user.admin_profile is not None
    except:
        return False


def is_super_admin(user):
    if not user.is_authenticated:
        return False
    try:
        return user.admin_profile.role == 'super_admin'
    except:
        return False


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin(request.user):
            logout(request)
            messages.error(request, 'انتهت جلستك. يرجى تسجيل الدخول مجدداً.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def super_admin_required(view_func):
    """Decorator للسوبر أدمن فقط"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_super_admin(request.user):
            messages.error(request, 'هذه الصفحة للمدير العام فقط.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ───── المصادقة ─────

def login_view(request):
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('dashboard')
    elif request.user.is_authenticated:
        logout(request)

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if not is_admin(user):
            messages.error(request, _('You do not have access to this panel.'))
            return redirect('login')
        login(request, user)
        messages.success(request, _('Welcome back!'))
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ───── لوحة التحكم ─────

@admin_required
def dashboard_view(request):
    today = timezone.now().date()
    from catalog.models import Book
    from circulation.models import Loan, Fine, BookRequest
    from django.db.models import Sum
    from decimal import Decimal

    # ───── الإيرادات الشهرية ─────
    monthly_members = Member.objects.filter(
        plan__plan_type='monthly',
        membership_start__month=today.month,
        membership_start__year=today.year,
    ).count()
    yearly_members = Member.objects.filter(
        plan__plan_type='yearly',
        membership_start__month=today.month,
        membership_start__year=today.year,
    ).count()
    monthly_revenue = Decimal(str(monthly_members)) * Decimal('2500')
    yearly_revenue = Decimal(str(yearly_members)) * Decimal('30000')

    # مبيعات عبر الطلبات (المنتسبون)
    member_sales = BookRequest.objects.filter(
        request_type='purchase',
        status='completed',
        created_at__month=today.month,
        created_at__year=today.year,
    ).aggregate(total=Sum('book__price'))['total'] or Decimal('0')

    # مبيعات مباشرة (الزوار)
    direct_sales = DirectSale.objects.filter(
        sold_at__month=today.month,
        sold_at__year=today.year,
    ).aggregate(total=Sum('price'))['total'] or Decimal('0')

    book_sales_revenue = member_sales + direct_sales

    visitor_loans_revenue = Loan.objects.filter(
        borrower_type='visitor',
        loan_date__month=today.month,
        loan_date__year=today.year,
    ).aggregate(total=Sum('visitor_fee'))['total'] or Decimal('0')

    fines_revenue = Fine.objects.filter(
        is_paid=True,
        paid_at__month=today.month,
        paid_at__year=today.year,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    total_revenue = monthly_revenue + yearly_revenue + book_sales_revenue + visitor_loans_revenue + fines_revenue

    context = {
        'total_members': Member.objects.filter(status='active').count(),
        'expired_members': Member.objects.filter(status='expired').count(),
        'expiring_soon': Member.objects.filter(
            membership_end__range=[today, today + timezone.timedelta(days=7)],
            status='active'
        ).count(),
        'total_books': Book.objects.count(),
        'active_loans': Loan.objects.filter(status='active').count(),
        'overdue_loans': Loan.objects.filter(status='overdue').count(),
        'unpaid_fines': Fine.objects.filter(is_paid=False).count(),
        # الإيرادات
        'monthly_revenue': monthly_revenue,
        'yearly_revenue': yearly_revenue,
        'book_sales_revenue': book_sales_revenue,
        'visitor_loans_revenue': visitor_loans_revenue,
        'fines_revenue': fines_revenue,
        'total_revenue': total_revenue,
    }
    return render(request, 'accounts/dashboard.html', context)

# ───── إدارة المنتسبين ─────

@admin_required
def member_list_view(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    members = Member.objects.select_related('user', 'plan').all()

    if query:
        members = members.filter(
            Q(full_name__icontains=query) |
            Q(membership_number__icontains=query) |
            Q(national_id__icontains=query)
        )
    if status:
        members = members.filter(status=status)

    return render(request, 'accounts/member_list.html', {
        'members': members,
        'query': query,
        'status': status,
    })


@admin_required
def member_detail_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    loans = member.loans.select_related(
        'book_copy__book').order_by('-loan_date')[:10]
    return render(request, 'accounts/member_detail.html', {
        'member': member,
        'loans': loans,
    })


@admin_required
def member_create_view(request):
    user_form = UserCreateForm(request.POST or None)
    member_form = MemberForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if user_form.is_valid() and member_form.is_valid():
            user = user_form.save()
            member = member_form.save(commit=False)
            member.user = user
            member.save()
            messages.success(request, _('Member created successfully.'))
            return redirect('member_detail', pk=member.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))

    return render(request, 'accounts/member_form.html', {
        'user_form': user_form,
        'member_form': member_form,
        'title': _('Add New Member'),
    })


@admin_required
def member_update_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    form = MemberForm(request.POST or None,
                      request.FILES or None, instance=member)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Member updated successfully.'))
        return redirect('member_detail', pk=member.pk)
    return render(request, 'accounts/member_form.html', {
        'member_form': form,
        'member': member,
        'title': _('Edit Member'),
    })


@admin_required
def member_suspend_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    member.status = 'suspended'
    member.save()
    messages.warning(request, _('Member has been suspended.'))
    return redirect('member_detail', pk=member.pk)


# ───── إدارة الإداريين (Super Admin فقط) ─────

@super_admin_required
def admin_list_view(request):
    admins = Admin.objects.select_related('user').all()
    return render(request, 'accounts/admin_list.html', {'admins': admins})


@super_admin_required
def admin_create_view(request):
    user_form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and user_form.is_valid():
        user = user_form.save()
        user.is_staff = True
        user.save()
        Admin.objects.create(user=user, role='librarian')
        messages.success(request, _('Admin created successfully.'))
        return redirect('admin_list')
    return render(request, 'accounts/admin_form.html', {
        'user_form': user_form,
        'title': _('Create New Admin'),
    })


@super_admin_required
def admin_delete_view(request, pk):
    admin = get_object_or_404(Admin, pk=pk)
    if request.method == 'POST':
        admin.user.delete()
        messages.success(request, _('Admin deleted successfully.'))
        return redirect('admin_list')
    return render(request, 'accounts/admin_confirm_delete.html', {
        'admin': admin
    })