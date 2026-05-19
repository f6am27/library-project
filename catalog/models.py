from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from accounts.models import Member


class Author(models.Model):
    full_name = models.CharField(_('full name'), max_length=200)
    nationality = models.CharField(_('nationality'), max_length=100,
                                   blank=True, null=True)
    bio = models.TextField(_('biography'), blank=True, null=True)

    class Meta:
        verbose_name = _('author')
        verbose_name_plural = _('authors')
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Category(models.Model):
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    LANGUAGE_CHOICES = [
        ('ar', _('Arabic')),
        ('fr', _('French')),
        ('en', _('English')),
        ('other', _('Other')),
    ]

    title = models.CharField(_('title'), max_length=300)
    author = models.ForeignKey(Author, on_delete=models.PROTECT,
                               related_name='books', verbose_name=_('author'))
    category = models.ForeignKey(Category, on_delete=models.PROTECT,
                                 related_name='books', verbose_name=_('category'))
    isbn = models.CharField(_('ISBN'), max_length=20,
                            blank=True, null=True, unique=True)
    language = models.CharField(_('language'), max_length=10,
                                choices=LANGUAGE_CHOICES, default='ar')
    year_published = models.PositiveIntegerField(_('year published'),
                                                 blank=True, null=True)
    description = models.TextField(_('description'), blank=True, null=True)
    cover_image = models.ImageField(_('cover image'), upload_to='books/covers/',
                                    blank=True, null=True)
    total_copies = models.PositiveIntegerField(_('total copies'), default=1)
    available_copies = models.PositiveIntegerField(_('available copies'), default=1)
    avg_rating = models.DecimalField(_('average rating'), max_digits=3,
                                     decimal_places=2, default=0.00)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    price = models.DecimalField(
    _('price'), 
    max_digits=10, 
    decimal_places=2,
    blank=True, 
    null=True,
    help_text=_('Leave empty if book is not for sale')
)
    whatsapp_number = models.CharField(
        _('WhatsApp number'),
        max_length=20,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('book')
        verbose_name_plural = _('books')
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.author}"

    def update_avg_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            total = sum(r.rating for r in reviews)
            self.avg_rating = round(total / reviews.count(), 2)
        else:
            self.avg_rating = 0.00
        self.save(update_fields=['avg_rating'])
        
    def available_loan_copies(self):
        return self.copies.filter(
            is_available=True,
            copy_type__in=['loan', 'both']
        ).count()

    def available_sale_copies(self):
        return self.copies.filter(
            is_available=True,
            copy_type__in=['sale', 'both']
        ).count()



class BookCopy(models.Model):
    CONDITION_CHOICES = [
        ('new', _('New')),
        ('good', _('Good')),
        ('fair', _('Fair')),
        ('damaged', _('Damaged')),
    ]
    COPY_TYPE_CHOICES = [
        ('loan', _('For loan')),
        ('sale', _('For sale')),
        ('both', _('For loan and sale')),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='copies', verbose_name=_('book'))
    copy_type = models.CharField(_('copy type'), max_length=10,
                                 choices=COPY_TYPE_CHOICES, default='loan')
    condition = models.CharField(_('condition'), max_length=10,
                                 choices=CONDITION_CHOICES, default='good')
    is_available = models.BooleanField(_('is available'), default=True)
    notes = models.TextField(_('notes'), blank=True, null=True)

    class Meta:
        verbose_name = _('book copy')
        verbose_name_plural = _('book copies')

    def __str__(self):
        return f"{self.book.title} — نسخة #{self.id} ({self.get_copy_type_display()})"


class Review(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE,
                               related_name='reviews', verbose_name=_('member'))
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='reviews', verbose_name=_('book'))
    rating = models.PositiveIntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_('comment'), blank=True, null=True)
    is_approved = models.BooleanField(_('is approved'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        unique_together = ('member', 'book')  # منتسب واحد = تقييم واحد لكل كتاب

    def __str__(self):
        return f"{self.member} — {self.book} ({self.rating}★)"