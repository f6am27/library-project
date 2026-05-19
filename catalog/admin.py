from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Author, Category, Book, BookCopy, Review


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'nationality')
    search_fields = ('full_name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class BookCopyInline(admin.TabularInline):
    model = BookCopy
    extra = 0
    fields = ('condition', 'is_available', 'notes')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'language',
                    'total_copies', 'available_copies', 'avg_rating')
    list_filter = ('category', 'language')
    search_fields = ('title', 'author__full_name', 'isbn')
    inlines = [BookCopyInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('member', 'book', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        for review in queryset:
            review.book.update_avg_rating()
    approve_reviews.short_description = _('Approve selected reviews')