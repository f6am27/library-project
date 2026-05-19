from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from catalog.models import Book, Category, Author
from circulation.models import Loan, BookRequest
from accounts.models import Member


# ───── دالة مساعدة ─────

def is_member(user):
    try:
        return hasattr(user, 'member_profile')
    except:
        return False


# ───── الصفحة الرئيسية ─────

def home_view(request):
    featured_books = Book.objects.filter(
        available_copies__gt=0
    ).order_by('-avg_rating')[:8]

    latest_books = Book.objects.order_by('-created_at')[:4]
    categories = Category.objects.all()[:6]

    context = {
        'featured_books': featured_books,
        'latest_books': latest_books,
        'categories': categories,
        'total_books': Book.objects.count(),
        'total_authors': Author.objects.count(),
        'whatsapp': getattr(settings, 'LIBRARY_WHATSAPP', ''),
    }
    return render(request, 'public/home.html', context)


# ───── تصفح الكتب ─────

def book_list_view(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    language = request.GET.get('language', '')
    availability = request.GET.get('availability', '')

    books = Book.objects.select_related('author', 'category').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__full_name__icontains=query) |
            Q(description__icontains=query)
        )
    if category_id:
        books = books.filter(category_id=category_id)
    if language:
        books = books.filter(language=language)
    if availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability == 'for_sale':
        books = books.filter(price__isnull=False)

    context = {
        'books': books,
        'categories': Category.objects.all(),
        'query': query,
        'selected_category': category_id,
        'selected_language': language,
        'selected_availability': availability,
        'total': books.count(),
    }
    return render(request, 'public/book_list.html', context)


# ───── تفاصيل الكتاب ─────

def book_detail_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.filter(is_approved=True).select_related('member')
    whatsapp = getattr(settings, 'LIBRARY_WHATSAPP', '')

    purchase_message = f"مرحباً، أريد شراء كتاب: {book.title}"
    purchase_url = f"https://wa.me/{whatsapp}?text={purchase_message}"
    inquiry_message = f"مرحباً، أريد الاستفسار عن كتاب: {book.title}"
    inquiry_url = f"https://wa.me/{whatsapp}?text={inquiry_message}"

    # ───── حساب النسخ بشكل منفصل ─────
    loan_copies_available = book.copies.filter(
        is_available=True, copy_type__in=['loan', 'both']
    ).count()
    sale_copies_available = book.copies.filter(
        is_available=True, copy_type__in=['sale', 'both']
    ).count()

    # هل المنتسب لديه طلب معلق؟
    existing_request = None
    has_active_loan = False
    if request.user.is_authenticated and is_member(request.user):
        existing_request = BookRequest.objects.filter(
            member=request.user.member_profile,
            book=book,
            status='pending'
        ).first()
        has_active_loan = request.user.member_profile.loans.filter(
            status__in=['active', 'overdue']
        ).exists()

    context = {
        'book': book,
        'reviews': reviews,
        'purchase_url': purchase_url,
        'inquiry_url': inquiry_url,
        'existing_request': existing_request,
        'loan_copies_available': loan_copies_available,
        'sale_copies_available': sale_copies_available,
        'has_active_loan': has_active_loan,
        'related_books': Book.objects.filter(
            category=book.category
        ).exclude(pk=pk)[:4],
    }
    return render(request, 'public/book_detail.html', context)

# ───── من نحن ─────

def about_view(request):
    whatsapp = getattr(settings, 'LIBRARY_WHATSAPP', '')
    context = {
        'total_books': Book.objects.count(),
        'total_authors': Author.objects.count(),
        'whatsapp': whatsapp,
        'whatsapp_url': f"https://wa.me/{whatsapp}",
    }
    return render(request, 'public/about.html', context)


# ───── تسجيل دخول المنتسب ─────

def member_login_view(request):
    if request.user.is_authenticated and is_member(request.user):
        return redirect('member_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user and is_member(user):
            login(request, user)
            return redirect('member_dashboard')
        elif user and not is_member(user):
            messages.error(request, 'هذا الحساب ليس حساب منتسب.')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')

    return render(request, 'public/member_login.html')


def member_logout_view(request):
    logout(request)
    return redirect('home')


# ───── لوحة المنتسب ─────

@login_required(login_url='/member/login/')
def member_dashboard_view(request):
    if not is_member(request.user):
        return redirect('home')

    member = request.user.member_profile
    active_loans = member.loans.filter(
        status__in=['active', 'overdue']
    ).select_related('book_copy__book').order_by('due_date')
    past_loans = member.loans.filter(
        status='returned'
    ).select_related('book_copy__book').order_by('-return_date')[:5]
    pending_requests = member.requests.filter(
        status='pending'
    ).select_related('book').order_by('-created_at')

    # ───── الغرامات غير المدفوعة ─────
    from circulation.models import Fine
    unpaid_fines = Fine.objects.filter(
        loan__member=member,
        is_paid=False
    ).select_related('loan__book_copy__book')

    context = {
        'member': member,
        'active_loans': active_loans,
        'past_loans': past_loans,
        'pending_requests': pending_requests,
        'unpaid_fines': unpaid_fines,
    }
    return render(request, 'public/member_dashboard.html', context)


# ───── طلب استعارة أو شراء ─────

@login_required(login_url='/member/login/')
def book_request_view(request, pk):
    if not is_member(request.user):
        return redirect('home')

    book = get_object_or_404(Book, pk=pk)
    member = request.user.member_profile
    request_type = request.GET.get('type', 'loan')

    # ───── التحقق من صلاحية الاشتراك ─────
    if request_type == 'loan':
        from django.utils import timezone
        if member.status != 'active' or member.membership_end < timezone.now().date():
            messages.error(
                request,
                f'اشتراكك منتهٍ منذ {member.membership_end}. يرجى التواصل مع المكتبة لتجديده.'
            )
            return redirect('public_book_detail', pk=pk)

        # التحقق من عدم وجود استعارة نشطة
        active_loan = member.loans.filter(status__in=['active', 'overdue']).first()
        if active_loan:
            messages.error(
                request,
                f'لديك كتاب مستعار حالياً: "{active_loan.book_copy.book.title}" — موعد إرجاعه {active_loan.due_date}'
            )
            return redirect('public_book_detail', pk=pk)

    # التحقق من عدم وجود طلب مسبق
    existing = BookRequest.objects.filter(
        member=member, book=book, status='pending'
    ).exists()
    if existing:
        messages.warning(request, 'لديك طلب معلق لهذا الكتاب بالفعل.')
        return redirect('public_book_detail', pk=pk)

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        BookRequest.objects.create(
            member=member,
            book=book,
            request_type=request_type,
            notes=notes,
        )
        from notifications.models import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(admin_profile__isnull=False)
        for admin_user in admins:
            Notification.send(
                user=admin_user,
                notification_type='new_reservation',
                title='طلب جديد',
                message=f'{member.full_name} طلب {"استعارة" if request_type == "loan" else "شراء"} كتاب: {book.title}',
                target_model='BookRequest',
            )
        messages.success(request, 'تم إرسال طلبك بنجاح! سيتواصل معك فريق المكتبة.')
        return redirect('member_dashboard')

    return render(request, 'public/book_request.html', {
        'book': book,
        'request_type': request_type,
    })