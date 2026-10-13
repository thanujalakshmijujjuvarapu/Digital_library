from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from .models import Book, Category, BorrowRecord, Review


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'isbn',
            'category',
            'publication_year',
            'publisher',
            'total_copies',
            'available_copies',
            'cover_image_url',
            'is_featured',
            'description',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Clean Code: A Handbook of Agile Software Craftsmanship'
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Robert C. Martin'
            }),
            'isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 978-0132350884'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'publication_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 2008',
                'min': '1400',
                'max': '2030'
            }),
            'publisher': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Prentice Hall'
            }),
            'total_copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'available_copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'cover_image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://images.example.com/books/cover.jpg'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Provide a concise overview or synopsis of the book...',
                'id': 'book-description-input'
            }),
        }

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn', '').strip()
        # Allow numbers and hyphens, strip hyphens for digit check
        clean_code = isbn.replace('-', '').replace(' ', '')
        if not (clean_code.isdigit() and len(clean_code) in (10, 13)):
            raise ValidationError("Please enter a valid 10-digit or 13-digit ISBN.")
        return isbn

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_copies')
        available = cleaned_data.get('available_copies')
        year = cleaned_data.get('publication_year')
        current_year = timezone.now().year + 1

        if year and (year < 1400 or year > current_year):
            self.add_error('publication_year', f"Publication year must be between 1400 and {current_year}.")

        if total is not None and available is not None:
            if available > total:
                self.add_error('available_copies', "Available copies cannot exceed total copies.")
            if total < 1:
                self.add_error('total_copies', "Total copies must be at least 1.")
            if available < 0:
                self.add_error('available_copies', "Available copies cannot be negative.")

        return cleaned_data


class BorrowForm(forms.Form):
    DURATION_CHOICES = [
        (7, '7 Days (1 Week)'),
        (14, '14 Days (2 Weeks - Standard)'),
        (21, '21 Days (3 Weeks)'),
        (30, '30 Days (1 Month - Maximum)'),
    ]

    loan_duration_days = forms.ChoiceField(
        choices=DURATION_CHOICES,
        initial=14,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'loanDurationSelect'
        }),
        help_text="Standard loan duration is 14 days."
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional loan note (e.g., Course study or Research project)'
        })
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-select',
                'id': 'reviewRatingSelect'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your personal review or critique of this book...',
                'id': 'reviewCommentInput',
                'maxlength': '1000'
            }),
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if len(comment) < 10:
            raise ValidationError("Review comment must be at least 10 characters long.")
        return comment


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Artificial Intelligence'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of this category...'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. bi-cpu, bi-book, bi-terminal'
            }),
        }


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@university.edu'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )

    class Meta(UserCreationForm.Meta):
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
