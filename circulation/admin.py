from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Loan, Fine, Reservation


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('member', 'book_copy', 'loan_date',
                    'due_date', 'return_date', 'status')
    list_filter = ('status',)
    search_fields = ('member__full_name', 'book_copy__book__title')


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'is_paid', 'paid_at', 'created_at')
    list_filter = ('is_paid',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('member', 'book', 'reserved_at', 'status', 'notified')
    list_filter = ('status',)