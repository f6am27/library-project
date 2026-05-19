from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Book, Author, Category, BookCopy, Review
import json

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['full_name', 'nationality', 'bio']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nationality'].required = False
        self.fields['bio'].required = False


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False


class BookForm(forms.ModelForm):
    # حقل نصي للمؤلف بدل القائمة المنسدلة
    author_name = forms.CharField(
        label=_('Author'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'author-input',
            'autocomplete': 'off',
            'placeholder': 'اكتب اسم المؤلف...',
        })
    )
    loan_copies = forms.IntegerField(
    label=_('Copies for loan'),
    min_value=0, initial=0,
    required=False,
    widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
    )
    sale_copies = forms.IntegerField(
        label=_('Copies for sale'),
        min_value=0, initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
    )

    class Meta:
        model = Book
        fields = [
            'title', 'category', 'language',
            'isbn', 'year_published', 'description',
            'cover_image', 'total_copies', 'price',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'year_published': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['isbn'].required = False
        self.fields['year_published'].required = False
        self.fields['description'].required = False
        self.fields['cover_image'].required = False
        self.fields['price'].required = False
        self.fields['total_copies'].required = False
        self.fields['total_copies'].widget = forms.HiddenInput()

        # إذا كان تعديل كتاب موجود
        if self.instance and self.instance.pk:
            # تعبئة اسم المؤلف
            if self.instance.author:
                self.fields['author_name'].initial = self.instance.author.full_name

            # ───── تعبئة عدد النسخ الحالية ─────
            self.fields['loan_copies'].initial = self.instance.copies.filter(
                copy_type__in=['loan', 'both']
            ).count()
            self.fields['sale_copies'].initial = self.instance.copies.filter(
                copy_type__in=['sale', 'both']
            ).count()

        # قائمة المؤلفين للـ autocomplete
        authors = list(Author.objects.values_list('full_name', flat=True))
        self.fields['author_name'].widget.attrs['data-authors'] = json.dumps(authors)

    def save(self, commit=True):
        book = super().save(commit=False)

        author_name = self.cleaned_data.get('author_name', '').strip()
        if author_name:
            author, created = Author.objects.get_or_create(
                full_name__iexact=author_name,
                defaults={'full_name': author_name}
            )
            book.author = author

        loan_copies = self.cleaned_data.get('loan_copies') or 0
        sale_copies = self.cleaned_data.get('sale_copies') or 0

        if commit:
            book.save()

            if self.instance.pk:
                # احذف فقط النسخ المتاحة وغير المستعارة
                book.copies.filter(
                    is_available=True,
                    copy_type='loan',
                    loans__isnull=True  # ← لا علاقة لها بأي استعارة
                ).delete()
                book.copies.filter(
                    is_available=True,
                    copy_type='sale',
                    loans__isnull=True
                ).delete()

            for i in range(loan_copies):
                BookCopy.objects.create(book=book, copy_type='loan')
            for i in range(sale_copies):
                BookCopy.objects.create(book=book, copy_type='sale')

            book.total_copies = book.copies.count()
            book.available_copies = book.copies.filter(is_available=True).count()
            book.save(update_fields=['total_copies', 'available_copies'])

        return book


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comment': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].required = False