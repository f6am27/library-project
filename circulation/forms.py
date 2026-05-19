from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Loan, Fine, Reservation
from catalog.models import BookCopy, Book
from accounts.models import Member
from django.db.models import Min



class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['member', 'book_copy', 'due_date', 'notes']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'book_copy': forms.Select(attrs={
                'class': 'form-select',
                'size': '1',
            }),           
            'due_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = Member.objects.filter(status='active')
        # نأخذ نسخة واحدة فقط لكل كتاب (أول نسخة متاحة)
        book_ids = BookCopy.objects.filter(
            is_available=True,
            copy_type__in=['loan', 'both']
        ).values('book').annotate(first_copy=Min('id')).values_list('first_copy', flat=True)

        self.fields['book_copy'].queryset = BookCopy.objects.filter(
            id__in=book_ids
        ).select_related('book').order_by('book__title')

        self.fields['book_copy'].label_from_instance = lambda obj: \
            f"{obj.book.title} ({obj.book.copies.filter(is_available=True, copy_type__in=['loan','both']).count()} نسخة متوفرة)"
        self.fields['notes'].required = False
        self.fields['due_date'].initial = (
            timezone.now().date() + timezone.timedelta(days=10)
        )

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        if member:
            active_loans = member.loans.filter(
                status__in=['active', 'overdue']
            ).count()
            if active_loans >= 1:
                raise forms.ValidationError(
                    'هذا المنتسب لديه كتاب مستعار حالياً. يجب إرجاعه أولاً قبل استعارة كتاب آخر.'
                )
        return cleaned_data


class ReturnForm(forms.Form):
    notes = forms.CharField(
        label=_('Notes'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    fine_amount = forms.DecimalField(
        label=_('Fine amount'),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    fine_reason = forms.CharField(
        label=_('Fine reason'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class FinePaymentForm(forms.ModelForm):
    class Meta:
        model = Fine
        fields = ['is_paid']

    def save(self, commit=True):
        fine = super().save(commit=False)
        if fine.is_paid:
            fine.paid_at = timezone.now()
        if commit:
            fine.save()
        return fine


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['member', 'book']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'book': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = Member.objects.filter(status='active')
        self.fields['book'].queryset = Book.objects.filter(available_copies=0)

class VisitorLoanForm(forms.Form):
    visitor_name = forms.CharField(
        label='اسم الزائر',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'الاسم الكامل'
        })
    )
    visitor_phone = forms.CharField(
        label='رقم الهاتف',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'رقم الهاتف'
        })
    )
    visitor_id_image = forms.ImageField(
    label='صورة الهوية',
    required=False,
    widget=forms.FileInput(attrs={'class': 'form-control'})
)
    book_copy = forms.ModelChoiceField(
        label='الكتاب',
        queryset=BookCopy.objects.filter(
            is_available=True,
            copy_type__in=['loan', 'both']
        ).select_related('book'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    due_date = forms.DateField(
        label='موعد الإرجاع',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    visitor_fee = forms.DecimalField(
        label='الرسوم (MRU)',
        initial=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        self.fields['due_date'].initial = (
            timezone.now().date() + timezone.timedelta(days=10)
        )
        # ───── تخصيص عرض الكتب ─────
        from django.db.models import Min
        book_ids = BookCopy.objects.filter(
            is_available=True,
            copy_type__in=['loan', 'both']
        ).values('book').annotate(first_copy=Min('id')).values_list('first_copy', flat=True)

        self.fields['book_copy'].queryset = BookCopy.objects.filter(
            id__in=book_ids
        ).select_related('book').order_by('book__title')

        self.fields['book_copy'].label_from_instance = lambda obj: \
            f"{obj.book.title} ({obj.book.copies.filter(is_available=True, copy_type__in=['loan','both']).count()} نسخة متوفرة)"