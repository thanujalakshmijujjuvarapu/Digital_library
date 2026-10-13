from django.contrib import admin
from .models import Category, Book, BorrowRecord, Review
from django.utils import timezone
from datetime import date


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'book_count_display', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def book_count_display(self, obj):
        return obj.books.count()
    book_count_display.short_description = "Total Books"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'author', 
        'category', 
        'isbn', 
        'publication_year', 
        'available_copies', 
        'total_copies', 
        'is_featured', 
        'created_at'
    )
    list_filter = ('category', 'is_featured', 'publication_year')
    search_fields = ('title', 'author', 'isbn', 'publisher')
    list_editable = ('available_copies', 'total_copies', 'is_featured')
    ordering = ('-created_at',)
    actions = ['restock_all_copies']

    @admin.action(description="Restock available copies to total copies")
    def restock_all_copies(self, request, queryset):
        for book in queryset:
            book.available_copies = book.total_copies
            book.save()
        self.message_user(request, f"{queryset.count()} book(s) successfully restocked.")


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = (
        'book', 
        'user', 
        'borrow_date', 
        'due_date', 
        'return_date', 
        'status', 
        'fine_amount'
    )
    list_filter = ('status', 'borrow_date', 'due_date')
    search_fields = ('book__title', 'user__username', 'user__email')
    ordering = ('-borrow_date',)
    actions = ['mark_as_returned']

    @admin.action(description="Mark selected loans as returned")
    def mark_as_returned(self, request, queryset):
        today = date.today()
        count = 0
        for record in queryset.filter(status__in=['borrowed', 'overdue']):
            record.status = 'returned'
            record.return_date = today
            record.save()
            # Restock copy
            book = record.book
            if book.available_copies < book.total_copies:
                book.available_copies += 1
                book.save()
            count += 1
        self.message_user(request, f"{count} loan record(s) marked as returned.")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')
    ordering = ('-created_at',)
