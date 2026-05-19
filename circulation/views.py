from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
import datetime
from .models import Loan, Fine, Reservation, BookRequest
from .forms import LoanForm, ReturnForm, FinePaymentForm, ReservationForm
from catalog.models import BookCopy
from accounts.models import Admin
from notifications.models import Notification
from accounts.views import admin_required


def get_admin(request):
    try:
        return Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        return None


# ───── الاستعارة ─────

@admin_required
def loan_list_view(request):
    status = request.GET.get('status', '')
    query = request.GET.get('q', '')
    loans = Loan.objects.select_related(
        'member', 'book_copy__book').order_by('-loan_date')

    if status:
        loans = loans.filter(status=status)
    if query:
        loans = loans.filter(
            Q(member__full_name__icontains=query) |
            Q(member__membership_number__icontains=query) |
            Q(book_copy__book__title__icontains=query)
        )

    today = timezone.now().date()
    loans.filter(status='active', due_date__lt=today).update(status='overdue')

    return render(request, 'circulation/loan_list.html', {
        'loans': loans,
        'status': status,
        'query': query,
    })


@admin_required 
def loan_create_view(request):
    form = LoanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        admin = get_admin(request)
        loan = form.save(commit=False)
        loan.issued_by = admin
        loan.save()

        copy = loan.book_copy
        copy.is_available = False
        copy.save()

        book = copy.book
        book.available_copies = book.copies.filter(is_available=True).count()
        book.save(update_fields=['available_copies'])

        Notification.send(
            user=request.user,
            notification_type='new_reservation',
            title=_('New Loan Created'),
            message=f"{loan.member.full_name} borrowed {loan.book_copy.book.title}",
            target_model='Loan',
            target_id=loan.id,
        )

        messages.success(request, _('Loan created successfully.'))
        return redirect('loan_list')

    return render(request, 'circulation/loan_form.html', {
        'form': form,
        'title': _('New Loan'),
    })


@admin_required 
def loan_return_view(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    form = ReturnForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        admin = get_admin(request)
        today = timezone.now().date()

        loan.return_date = today
        loan.returned_to = admin
        loan.status = 'returned'
        loan.save()

        copy = loan.book_copy
        copy.is_available = True
        copy.save()

        book = copy.book
        book.available_copies = book.copies.filter(is_available=True).count()
        book.save(update_fields=['available_copies'])

        fine_amount = form.cleaned_data.get('fine_amount')
        if fine_amount and fine_amount > 0:
            Fine.objects.create(
                loan=loan,
                amount=fine_amount,
                reason=form.cleaned_data.get('fine_reason', ''),
            )

        reservation = Reservation.objects.filter(
            book=book, status='pending'
        ).order_by('reserved_at').first()
        if reservation:
            reservation.status = 'ready'
            reservation.notified = True
            reservation.save()
            Notification.send(
                user=reservation.member.user,
                notification_type='reservation_ready',
                title=_('Book Available'),
                message=f"{book.title} is now available for pickup.",
                target_model='Reservation',
                target_id=reservation.id,
            )

        messages.success(request, _('Book returned successfully.'))
        return redirect('loan_list')

    return render(request, 'circulation/loan_return.html', {
        'loan': loan,
        'form': form,
        'days_overdue': loan.days_overdue(),
    })


@admin_required 
def loan_detail_view(request, pk):
    loan = get_object_or_404(
        Loan.objects.select_related(
            'member', 'book_copy__book', 'issued_by__user'
        ), pk=pk
    )
    return render(request, 'circulation/loan_detail.html', {'loan': loan})


# ───── الغرامات ─────

@admin_required 
def fine_list_view(request):
    fines = Fine.objects.filter(
        is_paid=False).select_related('loan__member', 'loan__book_copy__book')
    return render(request, 'circulation/fine_list.html', {'fines': fines})


@admin_required 
def fine_pay_view(request, pk):
    fine = get_object_or_404(Fine, pk=pk)
    fine.is_paid = True
    fine.paid_at = timezone.now()
    fine.save()
    messages.success(request, _('Fine marked as paid.'))
    return redirect('fine_list')


# ───── الحجوزات ─────

@admin_required 
def reservation_list_view(request):
    reservations = Reservation.objects.select_related(
        'member', 'book').order_by('reserved_at')
    return render(request, 'circulation/reservation_list.html', {
        'reservations': reservations,
    })


@admin_required 
def reservation_create_view(request):
    form = ReservationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Reservation created successfully.'))
        return redirect('reservation_list')
    return render(request, 'circulation/reservation_form.html', {
        'form': form,
        'title': _('New Reservation'),
    })


@admin_required 
def reservation_cancel_view(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    reservation.status = 'cancelled'
    reservation.save()
    messages.warning(request, _('Reservation cancelled.'))
    return redirect('reservation_list')


# ───── إدارة الطلبات ─────

@admin_required 
def request_list_view(request):
    status = request.GET.get('status', 'pending')
    requests = BookRequest.objects.select_related(
        'member', 'book__author'
    ).filter(status=status).order_by('-created_at')

    return render(request, 'circulation/request_list.html', {
        'requests': requests,
        'status': status,
        'pending_count': BookRequest.objects.filter(status='pending').count(),
        'status_tabs': [
            ('pending', 'معلقة'),
            ('approved', 'موافق عليها'),
            ('completed', 'مكتملة'),
            ('rejected', 'مرفوضة'),
        ],
    })


@admin_required 
def request_approve_loan_view(request, pk):
    book_request = get_object_or_404(BookRequest, pk=pk)
    admin = get_admin(request)

    # التحقق أن المنتسب ليس لديه استعارة نشطة
    active_loans = book_request.member.loans.filter(
        status__in=['active', 'overdue']
    ).count()
    if active_loans >= 1:
        messages.error(
            request,
            f'{book_request.member.full_name} لديه كتاب مستعار حالياً. يجب إرجاعه أولاً.'
        )
        return redirect('request_list')

    # إيجاد نسخة متاحة للاستعارة
    copy = book_request.book.copies.filter(
        is_available=True,
        copy_type__in=['loan', 'both']
    ).first()

    if not copy:
        messages.error(request, 'لا توجد نسخ متاحة للاستعارة حالياً.')
        return redirect('request_list')

    # إنشاء سجل الاستعارة تلقائياً
    loan = Loan.objects.create(
        member=book_request.member,
        book_copy=copy,
        issued_by=admin,
        loan_date=timezone.now().date(),
        due_date=timezone.now().date() + datetime.timedelta(days=10),
        status='active',
    )

    copy.is_available = False
    copy.save()

    book = book_request.book
    book.available_copies = book.copies.filter(is_available=True).count()
    book.save(update_fields=['available_copies'])

    book_request.status = 'completed'
    book_request.save()

    Notification.send(
        user=book_request.member.user,
        notification_type='reservation_ready',
        title='تم تأكيد طلب الاستعارة',
        message=f'تم تأكيد استعارة كتاب "{book.title}". موعد الإرجاع: {loan.due_date}',
        target_model='Loan',
        target_id=loan.id,
    )

    messages.success(request, 'تم تأكيد الاستعارة وإنشاء سجلها تلقائياً.')
    return redirect('request_list')


@admin_required 
def request_approve_sale_view(request, pk):
    book_request = get_object_or_404(BookRequest, pk=pk)

    copy = book_request.book.copies.filter(
        is_available=True,
        copy_type__in=['sale', 'both']
    ).first()

    if not copy:
        messages.error(request, 'لا توجد نسخ متاحة للبيع حالياً.')
        return redirect('request_list')

    copy.is_available = False
    copy.save()

    book = book_request.book
    book.available_copies = book.copies.filter(is_available=True).count()
    book.save(update_fields=['available_copies'])

    book_request.status = 'completed'
    book_request.save()

    Notification.send(
        user=book_request.member.user,
        notification_type='reservation_ready',
        title='تم تأكيد طلب الشراء',
        message=f'تم تأكيد بيع كتاب "{book.title}". شكراً لتعاملكم معنا.',
        target_model='BookRequest',
        target_id=book_request.id,
    )

    messages.success(request, 'تم تأكيد البيع وتحديث المخزون تلقائياً.')
    return redirect('request_list')


@admin_required 
def request_reject_view(request, pk):
    book_request = get_object_or_404(BookRequest, pk=pk)
    book_request.status = 'rejected'
    book_request.save()

    Notification.send(
        user=book_request.member.user,
        notification_type='loan_overdue',
        title='تم رفض طلبك',
        message=f'نأسف، تم رفض طلبك لكتاب "{book_request.book.title}". تواصل معنا للمزيد.',
        target_model='BookRequest',
        target_id=book_request.id,
    )

    messages.warning(request, 'تم رفض الطلب.')
    return redirect('request_list')


@admin_required
def visitor_loan_view(request):
    from .forms import VisitorLoanForm
    form = VisitorLoanForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        admin = get_admin(request)
        copy = form.cleaned_data['book_copy']

        loan = Loan.objects.create(
            member=None,
            book_copy=copy,
            issued_by=admin,
            borrower_type='visitor',
            visitor_name=form.cleaned_data['visitor_name'],
            visitor_phone=form.cleaned_data.get('visitor_phone', ''),
            visitor_fee=form.cleaned_data['visitor_fee'],
            visitor_id_image=form.cleaned_data.get('visitor_id_image'),
            loan_date=timezone.now().date(),
            due_date=form.cleaned_data['due_date'],
            status='active',
        )

        copy.is_available = False
        copy.save()

        book = copy.book
        book.available_copies = book.copies.filter(is_available=True).count()
        book.save(update_fields=['available_copies'])

        messages.success(
            request,
            f'تم تسجيل استعارة الزائر {loan.visitor_name} بنجاح.'
        )
        return redirect('loan_list')

    return render(request, 'circulation/visitor_loan_form.html', {
        'form': form,
        'title': 'استعارة زائر',
    })


@admin_required
def direct_sale_view(request):
    from catalog.models import Book
    from .models import DirectSale
    books = Book.objects.filter(
        price__isnull=False
    ).prefetch_related('copies')

    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        buyer_name = request.POST.get('buyer_name', 'زائر')
        book = get_object_or_404(Book, pk=book_id)
        admin = get_admin(request)

        copy = book.copies.filter(
            is_available=True,
            copy_type__in=['sale', 'both']
        ).first()

        if not copy:
            messages.error(request, 'لا توجد نسخ للبيع متاحة لهذا الكتاب.')
            return redirect('direct_sale')

        # تسجيل النسخة كغير متاحة
        copy.is_available = False
        copy.save()

        book.available_copies = book.copies.filter(is_available=True).count()
        book.save(update_fields=['available_copies'])

        # ───── تسجيل البيع في السجل ─────
        DirectSale.objects.create(
            book=book,
            buyer_name=buyer_name,
            price=book.price,
            sold_by=admin,
        )

        messages.success(
            request,
            f'تم تسجيل بيع كتاب "{book.title}" بنجاح. السعر: {book.price} MRU'
        )
        return redirect('direct_sale')

    return render(request, 'circulation/direct_sale.html', {
        'books': books,
        'title': 'تسجيل بيع مباشر',
    })