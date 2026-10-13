from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, 
        default="bi-journal-bookmark",
        help_text="Bootstrap icon class (e.g. bi-cpu, bi-book, bi-gear)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def book_count(self):
        return self.books.count()


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=200)
    isbn = models.CharField(
        max_length=20, 
        unique=True, 
        help_text="Valid 10 or 13-digit ISBN (hyphens allowed)"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='books'
    )
    description = models.TextField()
    publication_year = models.PositiveIntegerField()
    publisher = models.CharField(max_length=150, blank=True)
    total_copies = models.PositiveIntegerField(default=5)
    available_copies = models.PositiveIntegerField(default=5)
    cover_image_url = models.URLField(
        blank=True, 
        default="", 
        help_text="Direct URL to book cover image"
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        current_year = timezone.now().year + 1
        if self.publication_year and (self.publication_year < 1400 or self.publication_year > current_year):
            raise ValidationError({'publication_year': f"Publication year must be between 1400 and {current_year}."})
        if self.available_copies > self.total_copies:
            raise ValidationError({'available_copies': "Available copies cannot exceed total copies."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            avg = sum(r.rating for r in reviews) / reviews.count()
            return round(avg, 1)
        return None

    @property
    def reviews_count(self):
        return self.reviews.count()


class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]

    DAILY_LATE_FEE = Decimal('0.50')  # $0.50 per day late

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_records')
    borrow_date = models.DateField(default=date.today)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-borrow_date', '-created_at']

    def __str__(self):
        return f"{self.user.username} borrowed {self.book.title} ({self.status})"

    def update_status_and_fine(self):
        """Update overdue status and recalculate fine dynamically."""
        today = date.today()
        if self.status == 'borrowed' and today > self.due_date:
            self.status = 'overdue'
            days_late = (today - self.due_date).days
            self.fine_amount = Decimal(days_late) * self.DAILY_LATE_FEE
            self.save(update_fields=['status', 'fine_amount'])
        elif self.status == 'overdue' and today <= self.due_date:
            self.status = 'borrowed'
            self.fine_amount = Decimal('0.00')
            self.save(update_fields=['status', 'fine_amount'])

    @property
    def is_past_due(self):
        if self.status == 'returned' and self.return_date:
            return self.return_date > self.due_date
        return date.today() > self.due_date

    @property
    def days_remaining(self):
        if self.status == 'returned':
            return 0
        diff = (self.due_date - date.today()).days
        return diff


class Review(models.Model):
    RATING_CHOICES = [
        (5, '★★★★★ (5/5) - Excellent'),
        (4, '★★★★☆ (4/5) - Very Good'),
        (3, '★★★☆☆ (3/5) - Good'),
        (2, '★★☆☆☆ (2/5) - Fair'),
        (1, '★☆☆☆☆ (1/5) - Poor'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(help_text="Share your thoughts about this book")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('book', 'user')

    def __str__(self):
        return f"{self.user.username}'s review on {self.book.title} ({self.rating}★)"
