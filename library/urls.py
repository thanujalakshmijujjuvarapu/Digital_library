from django.urls import path
from . import views

urlpatterns = [
    # Catalog
    path('', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    
    # Book CRUD (Staff)
    path('books/add/', views.book_create, name='book_create'),
    path('books/<int:pk>/edit/', views.book_update, name='book_update'),
    path('books/<int:pk>/delete/', views.book_delete, name='book_delete'),
    
    # Borrow & Loans
    path('books/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('loans/<int:pk>/return/', views.return_book, name='return_book'),
    path('loans/<int:pk>/renew/', views.renew_book, name='renew_book'),
    path('my-loans/', views.my_loans, name='my_loans'),
    path('manage-loans/', views.manage_loans, name='manage_loans'),
    
    # Reviews
    path('books/<int:pk>/reviews/add/', views.add_review, name='add_review'),
    path('reviews/<int:pk>/delete/', views.delete_review, name='delete_review'),
    
    # Categories
    path('categories/add/', views.category_create, name='category_create'),
    
    # Auth
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # JavaScript API endpoint for live dynamic search
    path('api/search/', views.api_books_search, name='api_books_search'),
]
