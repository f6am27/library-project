from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import Book, Author, Category, BookCopy, Review
from .forms import BookForm, AuthorForm, CategoryForm, ReviewForm
from accounts.views import admin_required

# ───── الكتب ─────

@admin_required
def book_list_view(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    language = request.GET.get('language', '')
    books = Book.objects.select_related('author', 'category').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__full_name__icontains=query) |
            Q(isbn__icontains=query)
        )
    if category_id:
        books = books.filter(category_id=category_id)
    if language:
        books = books.filter(language=language)

    return render(request, 'catalog/book_list.html', {
        'books': books,
        'categories': Category.objects.all(),
        'query': query,
        'selected_category': category_id,
        'selected_language': language,
    })


@admin_required
def book_detail_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    copies = book.copies.all()
    reviews = book.reviews.filter(is_approved=True).select_related('member')
    return render(request, 'catalog/book_detail.html', {
        'book': book,
        'copies': copies,
        'reviews': reviews,
    })


@admin_required
def book_create_view(request):
    form = BookForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            book = form.save(commit=False)

            # ───── رفع الصورة مباشرة لـ Cloudinary ─────
            if 'cover_image' in request.FILES:
                try:
                    import cloudinary.uploader
                    image_file = request.FILES['cover_image']
                    upload_result = cloudinary.uploader.upload(
                        image_file,
                        folder='books/covers',
                        resource_type='image',
                    )
                    book.cover_image = upload_result['public_id']
                except Exception as e:
                    messages.warning(request, f'تعذر رفع الصورة: {e}')

            book.save()
            # حفظ النسخ (loan/sale copies) من الـ form
            form.instance = book
            loan_copies = form.cleaned_data.get('loan_copies') or 0
            sale_copies = form.cleaned_data.get('sale_copies') or 0
            for i in range(loan_copies):
                BookCopy.objects.create(book=book, copy_type='loan')
            for i in range(sale_copies):
                BookCopy.objects.create(book=book, copy_type='sale')
            book.total_copies = book.copies.count()
            book.available_copies = book.copies.filter(is_available=True).count()
            book.save(update_fields=['total_copies', 'available_copies'])

            messages.success(request, _('Book added successfully.'))
            return redirect('book_detail', pk=book.pk)
        else:
            print("Form errors:", form.errors)
    return render(request, 'catalog/book_form.html', {
        'form': form,
        'title': _('Add New Book'),
    })


@admin_required
def book_update_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None,
                    request.FILES or None, instance=book)
    if request.method == 'POST' and form.is_valid():

        # ───── رفع الصورة مباشرة لـ Cloudinary ─────
        if 'cover_image' in request.FILES:
            try:
                import cloudinary.uploader
                image_file = request.FILES['cover_image']
                upload_result = cloudinary.uploader.upload(
                    image_file,
                    folder='books/covers',
                    resource_type='image',
                )
                book.cover_image = upload_result['public_id']
                book.save(update_fields=['cover_image'])
            except Exception as e:
                messages.warning(request, f'تعذر رفع الصورة: {e}')

        form.save()
        messages.success(request, _('Book updated successfully.'))
        return redirect('book_detail', pk=book.pk)
    return render(request, 'catalog/book_form.html', {
        'form': form,
        'book': book,
        'title': _('Edit Book'),
    })


@admin_required
def book_delete_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, _('Book deleted successfully.'))
        return redirect('book_list')
    return render(request, 'catalog/book_confirm_delete.html', {'book': book})


# ───── المؤلفون ─────

@admin_required
def author_list_view(request):
    query = request.GET.get('q', '')
    authors = Author.objects.all()
    if query:
        authors = authors.filter(full_name__icontains=query)
    return render(request, 'catalog/author_list.html', {
        'authors': authors,
        'query': query,
    })


@admin_required
def author_create_view(request):
    form = AuthorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Author added successfully.'))
        return redirect('author_list')
    return render(request, 'catalog/author_form.html', {
        'form': form,
        'title': _('Add Author'),
    })


@admin_required
def author_update_view(request, pk):
    author = get_object_or_404(Author, pk=pk)
    form = AuthorForm(request.POST or None, instance=author)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Author updated successfully.'))
        return redirect('author_list')
    return render(request, 'catalog/author_form.html', {
        'form': form,
        'title': _('Edit Author'),
    })


# ───── التصنيفات ─────

@admin_required
def category_list_view(request):
    categories = Category.objects.all()
    return render(request, 'catalog/category_list.html', {
        'categories': categories,
    })


@admin_required
def category_create_view(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('Category added successfully.'))
        return redirect('category_list')
    return render(request, 'catalog/category_form.html', {
        'form': form,
        'title': _('Add Category'),
    })


# ───── التقييمات ─────

@admin_required
def review_list_view(request):
    reviews = Review.objects.filter(
        is_approved=False).select_related('member', 'book')
    return render(request, 'catalog/review_list.html', {
        'reviews': reviews,
    })


@admin_required
def review_approve_view(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_approved = True
    review.save()
    review.book.update_avg_rating()
    messages.success(request, _('Review approved.'))
    return redirect('review_list')


@admin_required
def review_reject_view(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.warning(request, _('Review rejected and deleted.'))
    return redirect('review_list')