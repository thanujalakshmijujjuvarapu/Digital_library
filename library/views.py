from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import Book, Category, BorrowRecord, Review
from .forms import BookForm, BorrowForm, ReviewForm, CategoryForm, UserRegisterForm


def is_librarian(user):
    """Check if the user is staff or superuser (librarian role)."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ==========================================
# CATALOG & DISCOVERY VIEWS
# ==========================================

def book_list(request):
    """
    Catalog Home: browse all books, search, filter by category and availability,
    and view live library statistics.
    """
    # Auto-update any overdue records for current active loans
    for record in BorrowRecord.objects.filter(status='borrowed', due_date__lt=date.today()):
        record.update_status_and_fine()

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    availability = request.GET.get('available', '').strip()
    sort = request.GET.get('sort', 'newest').strip()

    books = Book.objects.select_related('category').prefetch_related('reviews').all()

    # Search filter
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query) |
            Q(publisher__icontains=query)
        )

    # Category filter
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        books = books.filter(category=selected_category)

    # Availability filter
    if availability == '1':
        books = books.filter(available_copies__gt=0)
    elif availability == '0':
        books = books.filter(available_copies=0)

    # Sorting
    if sort == 'title':
        books = books.order_by('title')
    elif sort == 'year':
        books = books.order_by('-publication_year')
    elif sort == 'oldest':
        books = books.order_by('created_at')
    else:  # newest default
        books = books.order_by('-created_at')

    # Aggregated stats for the Hero section
    total_books_count = Book.objects.count()
    total_copies_count = sum(b.total_copies for b in Book.objects.all()) if total_books_count else 0
    active_loans_count = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count()
    categories_list = Category.objects.annotate(total_books=Count('books')).all()
    featured_books = Book.objects.filter(is_featured=True)[:4]

    context = {
        'books': books,
        'categories': categories_list,
        'selected_category': selected_category,
        'query': query,
        'availability': availability,
        'sort': sort,
        'featured_books': featured_books,
        'total_books_count': total_books_count,
        'total_copies_count': total_copies_count,
        'active_loans_count': active_loans_count,
    }
    return render(request, 'library/book_list.html', context)


def book_detail(request, pk):
    """
    Book Details: comprehensive book information, user borrowing status,
    loan dynamic calculation modal, reviews list, and review submission.
    """
    book = get_object_or_404(Book.objects.select_related('category'), pk=pk)
    reviews = book.reviews.select_related('user').all()
    
    # Check if user already borrowed this book and hasn't returned it
    user_active_loan = None
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_active_loan = BorrowRecord.objects.filter(
            book=book,
            user=request.user,
            status__in=['borrowed', 'overdue']
        ).first()
        user_has_reviewed = reviews.filter(user=request.user).exists()

    borrow_form = BorrowForm()
    review_form = ReviewForm()

    # Related books in the same category
    related_books = Book.objects.filter(
        category=book.category
    ).exclude(pk=book.pk)[:3] if book.category else []

    context = {
        'book': book,
        'reviews': reviews,
        'user_active_loan': user_active_loan,
        'user_has_reviewed': user_has_reviewed,
        'borrow_form': borrow_form,
        'review_form': review_form,
        'related_books': related_books,
    }
    return render(request, 'library/book_detail.html', context)


# ==========================================
# BOOK CRUD OPERATIONS (LIBRARIAN / STAFF)
# ==========================================

@user_passes_test(is_librarian, login_url='login')
def book_create(request):
    """Staff only: Add a new book to the library catalog."""
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' was successfully added to the catalog!")
            return redirect('book_detail', pk=book.pk)
        else:
            messages.error(request, "Please correct the errors in the form before submitting.")
    else:
        form = BookForm()

    return render(request, 'library/book_form.html', {'form': form, 'title': 'Add New Book', 'action': 'Add'})


@user_passes_test(is_librarian, login_url='login')
def book_update(request, pk):
    """Staff only: Edit existing book details and stock."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f"Book '{book.title}' was updated successfully!")
            return redirect('book_detail', pk=book.pk)
        else:
            messages.error(request, "Please correct the errors in the form before saving changes.")
    else:
        form = BookForm(instance=book)

    return render(request, 'library/book_form.html', {
        'form': form, 
        'book': book, 
        'title': f"Edit Book: {book.title}", 
        'action': 'Save Changes'
    })


@user_passes_test(is_librarian, login_url='login')
def book_delete(request, pk):
    """Staff only: Delete a book from the catalog."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f"Book '{title}' was permanently deleted from the catalog.")
        return redirect('book_list')

    return render(request, 'library/book_confirm_delete.html', {'book': book})


# ==========================================
# BORROWING & LOAN OPERATIONS
# ==========================================

@login_required(login_url='login')
def borrow_book(request, pk):
    """Authenticated user: Borrow an available book copy."""
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            # Check availability
            if book.available_copies <= 0:
                messages.error(request, f"Sorry, '{book.title}' is currently checked out completely.")
                return redirect('book_detail', pk=book.pk)

            # Check if user already has an active loan of this book
            existing_loan = BorrowRecord.objects.filter(
                book=book,
                user=request.user,
                status__in=['borrowed', 'overdue']
            ).first()

            if existing_loan:
                messages.warning(
                    request, 
                    f"You already have an active loan for this book (Due: {existing_loan.due_date})."
                )
                return redirect('book_detail', pk=book.pk)

            # Process borrow
            duration_days = int(form.cleaned_data['loan_duration_days'])
            notes = form.cleaned_data.get('notes', '')
            borrow_date = date.today()
            due_date = borrow_date + timedelta(days=duration_days)

            # Deduct copy
            book.available_copies -= 1
            book.save(update_fields=['available_copies'])

            record = BorrowRecord.objects.create(
                book=book,
                user=request.user,
                borrow_date=borrow_date,
                due_date=due_date,
                status='borrowed',
                notes=notes
            )

            messages.success(
                request, 
                f"Congratulations! You successfully borrowed '{book.title}'. Due date: {due_date.strftime('%B %d, %Y')}."
            )
            return redirect('my_loans')
        else:
            messages.error(request, "Invalid borrow form submission.")
            return redirect('book_detail', pk=book.pk)

    return redirect('book_detail', pk=book.pk)


@login_required(login_url='login')
def return_book(request, pk):
    """
    Return a borrowed book.
    Can be performed by the borrower or by a librarian.
    """
    record = get_object_or_404(BorrowRecord, pk=pk)

    # Permission check: borrower or librarian
    if record.user != request.user and not is_librarian(request.user):
        return HttpResponseForbidden("You do not have permission to return this book.")

    if request.method == 'POST':
        if record.status == 'returned':
            messages.info(request, "This book has already been returned.")
            return redirect('my_loans')

        today = date.today()
        record.return_date = today
        
        # Calculate late fee if overdue
        if today > record.due_date:
            days_late = (today - record.due_date).days
            record.fine_amount = Decimal(days_late) * BorrowRecord.DAILY_LATE_FEE
            record.status = 'returned'
            fine_msg = f" (Overdue by {days_late} days. Late fee: ${record.fine_amount})"
        else:
            record.status = 'returned'
            fine_msg = ""

        record.save()

        # Restock book copy
        book = record.book
        if book.available_copies < book.total_copies:
            book.available_copies += 1
            book.save(update_fields=['available_copies'])

        messages.success(request, f"'{book.title}' has been returned successfully!{fine_msg}")

        if is_librarian(request.user) and request.POST.get('from_manage'):
            return redirect('manage_loans')
        return redirect('my_loans')

    return redirect('my_loans')


@login_required(login_url='login')
def renew_book(request, pk):
    """Renew an active loan: extends due date by 7 additional days."""
    record = get_object_or_404(BorrowRecord, pk=pk)

    if record.user != request.user and not is_librarian(request.user):
        return HttpResponseForbidden("You do not have permission to renew this loan.")

    if request.method == 'POST':
        if record.status != 'borrowed':
            messages.error(request, "Only currently active non-overdue loans can be renewed.")
            return redirect('my_loans')

        # Extend due date by 7 days
        record.due_date += timedelta(days=7)
        record.save(update_fields=['due_date'])

        messages.success(
            request, 
            f"Loan extended! New due date for '{record.book.title}' is {record.due_date.strftime('%B %d, %Y')}."
        )

    return redirect('my_loans')


@login_required(login_url='login')
def my_loans(request):
    """User Dashboard: Displays active loans, overdue notifications, past loan history, and fines."""
    records = BorrowRecord.objects.filter(user=request.user).select_related('book', 'book__category')

    # Update overdue status on active loans
    for r in records.filter(status='borrowed'):
        r.update_status_and_fine()

    active_loans = records.filter(status__in=['borrowed', 'overdue'])
    returned_loans = records.filter(status='returned')
    total_fines = sum(r.fine_amount for r in records)

    context = {
        'active_loans': active_loans,
        'returned_loans': returned_loans,
        'total_fines': total_fines,
    }
    return render(request, 'library/my_loans.html', context)


@user_passes_test(is_librarian, login_url='login')
def manage_loans(request):
    """Staff only: Librarian dashboard to manage all member loans across the entire library."""
    # Update overdue records first
    for r in BorrowRecord.objects.filter(status='borrowed', due_date__lt=date.today()):
        r.update_status_and_fine()

    status_filter = request.GET.get('status', 'all').strip()
    search_query = request.GET.get('q', '').strip()

    loans = BorrowRecord.objects.select_related('book', 'user', 'book__category').all()

    if status_filter in ['borrowed', 'overdue', 'returned']:
        loans = loans.filter(status=status_filter)

    if search_query:
        loans = loans.filter(
            Q(book__title__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # Statistics
    total_active = BorrowRecord.objects.filter(status='borrowed').count()
    total_overdue = BorrowRecord.objects.filter(status='overdue').count()
    total_returned = BorrowRecord.objects.filter(status='returned').count()
    total_fines_accrued = sum(r.fine_amount for r in BorrowRecord.objects.all())

    context = {
        'loans': loans,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_active': total_active,
        'total_overdue': total_overdue,
        'total_returned': total_returned,
        'total_fines_accrued': total_fines_accrued,
    }
    return render(request, 'library/manage_loans.html', context)


# ==========================================
# REVIEWS & RATINGS
# ==========================================

@login_required(login_url='login')
def add_review(request, pk):
    """Add a review and star rating for a book."""
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Check if user already reviewed
            existing = Review.objects.filter(book=book, user=request.user).first()
            if existing:
                messages.warning(request, "You have already reviewed this book.")
                return redirect('book_detail', pk=book.pk)

            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.save()

            messages.success(request, "Thank you! Your book review has been published.")
        else:
            for error in form.errors.values():
                messages.error(request, error)

    return redirect('book_detail', pk=book.pk)


@login_required(login_url='login')
def delete_review(request, pk):
    """Delete a user's own review."""
    review = get_object_or_404(Review, pk=pk)
    if review.user != request.user and not is_librarian(request.user):
        return HttpResponseForbidden("You do not have permission to delete this review.")

    book_pk = review.book.pk
    review.delete()
    messages.success(request, "Your review has been removed.")
    return redirect('book_detail', pk=book_pk)


# ==========================================
# CATEGORY MANAGEMENT (STAFF)
# ==========================================

@user_passes_test(is_librarian, login_url='login')
def category_create(request):
    """Create a new book category."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' created successfully!")
            return redirect('book_list')
        else:
            messages.error(request, "Please check the category form inputs.")
    else:
        form = CategoryForm()

    return render(request, 'library/category_form.html', {'form': form})


# ==========================================
# USER AUTHENTICATION
# ==========================================

def user_register(request):
    """Register a new student / reader account."""
    if request.user.is_authenticated:
        return redirect('book_list')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Digital Library Hub, {user.first_name or user.username}! Your account is now active.")
            return redirect('book_list')
        else:
            messages.error(request, "Registration could not be completed. Please review the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'library/register.html', {'form': form})


def user_login(request):
    """Login existing member or librarian."""
    if request.user.is_authenticated:
        return redirect('book_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('book_list')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'library/login.html', {'form': form})


def user_logout(request):
    """Logout current user."""
    logout(request)
    messages.info(request, "You have been logged out successfully. See you again soon!")
    return redirect('book_list')


# ==========================================
# DYNAMIC JSON API (FOR JAVASCRIPT FEATURES)
# ==========================================

def api_books_search(request):
    """
    Live Search JSON Endpoint:
    Returns book matches for real-time client-side search autocomplete and instant filtering.
    """
    q = request.GET.get('q', '').strip()
    books = Book.objects.select_related('category').all()

    if q:
        books = books.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(isbn__icontains=q)
        )

    data = [
        {
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'isbn': b.isbn,
            'category': b.category.name if b.category else 'Uncategorized',
            'available_copies': b.available_copies,
            'total_copies': b.total_copies,
            'year': b.publication_year,
            'cover_image_url': b.cover_image_url,
            'detail_url': f"/books/{b.id}/"
        }
        for b in books[:12]
    ]
    return JsonResponse({'results': data, 'count': len(data)})
