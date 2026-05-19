from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import Member, Admin
from catalog.models import Book, BookCopy


class Loan(models.Model):
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('returned', _('Returned')),
        ('overdue', _('Overdue')),
        ('lost', _('Lost')),
    ]

    member = models.ForeignKey(Member, on_delete=models.PROTECT,
                               related_name='loans', verbose_name=_('member'),
                               blank=True, null=True)
    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT,
                                  related_name='loans', verbose_name=_('book copy'))
    issued_by = models.ForeignKey(Admin, on_delete=models.PROTECT,
                                  related_name='issued_loans',
                                  verbose_name=_('issued by'))
    returned_to = models.ForeignKey(Admin, on_delete=models.PROTECT,
                                    related_name='received_loans',
                                    verbose_name=_('returned to'),
                                    blank=True, null=True)
    loan_date = models.DateField(_('loan date'), default=timezone.now)
    due_date = models.DateField(_('due date'))
    return_date = models.DateField(_('return date'), blank=True, null=True)
    status = models.CharField(_('status'), max_length=10,
                              choices=STATUS_CHOICES, default='active')
    notes = models.TextField(_('notes'), blank=True, null=True)

    # ───── استعارة الزوار ─────
    BORROWER_TYPE = [
        ('member', _('Member')),
        ('visitor', _('Visitor')),
    ]
    borrower_type = models.CharField(
        _('borrower type'), max_length=10,
        choices=BORROWER_TYPE, default='member'
    )
    visitor_name = models.CharField(
        _('visitor name'), max_length=150,
        blank=True, null=True
    )
    visitor_phone = models.CharField(
        _('visitor phone'), max_length=20,
        blank=True, null=True
    )
    visitor_id_image = models.ImageField(
    _('visitor ID image'),
    upload_to='visitors/ids/',
    blank=True, null=True
)
    visitor_fee = models.DecimalField(
        _('visitor fee'), max_digits=8, decimal_places=2,
        default=100.00, blank=True, null=True
    )

    class Meta:
        verbose_name = _('loan')
        verbose_name_plural = _('loans')
        ordering = ['-loan_date']

    def __str__(self):
        return f"{self.member} — {self.book_copy.book.title}"

    def is_overdue(self):
        if self.status == 'active' and self.due_date < timezone.now().date():
            return True
        return False

    def days_overdue(self):
        if self.is_overdue():
            return (timezone.now().date() - self.due_date).days
        return 0


class Fine(models.Model):
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE,
                                related_name='fine', verbose_name=_('loan'))
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    reason = models.TextField(_('reason'), blank=True, null=True)
    is_paid = models.BooleanField(_('is paid'), default=False)
    paid_at = models.DateTimeField(_('paid at'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('fine')
        verbose_name_plural = _('fines')

    def __str__(self):
        return f"Fine for {self.loan} — {self.amount} MRU"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('ready', _('Ready for pickup')),
        ('cancelled', _('Cancelled')),
        ('fulfilled', _('Fulfilled')),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE,
                               related_name='reservations',
                               verbose_name=_('member'))
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='reservations',
                             verbose_name=_('book'))
    reserved_at = models.DateTimeField(_('reserved at'), auto_now_add=True)
    status = models.CharField(_('status'), max_length=15,
                              choices=STATUS_CHOICES, default='pending')
    notified = models.BooleanField(_('notified'), default=False)

    class Meta:
        verbose_name = _('reservation')
        verbose_name_plural = _('reservations')
        ordering = ['reserved_at']
        unique_together = ('member', 'book')  # حجز واحد لكل كتاب لكل منتسب

    def __str__(self):
        return f"{self.member} — {self.book.title} ({self.get_status_display()})"
    
class BookRequest(models.Model):
    REQUEST_TYPES = [
        ('loan', _('Loan request')),
        ('purchase', _('Purchase request')),
    ]
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('completed', _('Completed')),
        ('rejected', _('Rejected')),
    ]
    member = models.ForeignKey(Member, on_delete=models.CASCADE,
                               related_name='requests', verbose_name=_('member'))
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='requests', verbose_name=_('book'))
    request_type = models.CharField(_('request type'), max_length=10,
                                    choices=REQUEST_TYPES)
    status = models.CharField(_('status'), max_length=10,
                              choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(_('notes'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('book request')
        verbose_name_plural = _('book requests')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member} — {self.book.title} ({self.get_request_type_display()})"
    

class DirectSale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT,
                             related_name='direct_sales', verbose_name=_('book'))
    buyer_name = models.CharField(_('buyer name'), max_length=150,
                                  blank=True, null=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    sold_by = models.ForeignKey(Admin, on_delete=models.PROTECT,
                                verbose_name=_('sold by'))
    sold_at = models.DateTimeField(_('sold at'), auto_now_add=True)

    class Meta:
        verbose_name = _('direct sale')
        verbose_name_plural = _('direct sales')
        ordering = ['-sold_at']

    def __str__(self):
        return f"{self.book.title} — {self.buyer_name or 'زائر'} — {self.price} MRU"