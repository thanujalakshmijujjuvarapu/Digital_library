from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from library.models import Book, Category, BorrowRecord, Review


class DigitalLibraryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='teststudent', password='testpassword123', email='test@example.com')
        self.staff_user = User.objects.create_user(username='librarian', password='staffpassword123', is_staff=True)
        self.category = Category.objects.create(name='Computer Science', slug='computer-science', description='CS books')
        self.book = Book.objects.create(
            title='Clean Code',
            author='Robert C. Martin',
            isbn='9780132350884',
            category=self.category,
            total_copies=5,
            available_copies=5,
            publication_year=2008,
            description='A handbook of agile software craftsmanship.'
        )

    def test_book_list_view(self):
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clean Code')

    def test_book_detail_view(self):
        response = self.client.get(reverse('book_detail', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clean Code')
        self.assertContains(response, 'Robert C. Martin')

    def test_api_books_search(self):
        response = self.client.get(reverse('api_books_search'), {'q': 'Clean'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['title'], 'Clean Code')

    def test_borrow_and_return_book(self):
        self.client.login(username='teststudent', password='testpassword123')
        borrow_response = self.client.post(reverse('borrow_book', kwargs={'pk': self.book.pk}), {
            'loan_duration_days': 14,
            'notes': 'Studying software design'
        }, follow=True)
        self.assertEqual(borrow_response.status_code, 200)

        # Book availability should decrease
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 4)

        # BorrowRecord exists
        record = BorrowRecord.objects.get(book=self.book, user=self.user)
        self.assertEqual(record.status, 'borrowed')

        # Return the book
        return_response = self.client.post(reverse('return_book', kwargs={'pk': record.pk}), follow=True)
        self.assertEqual(return_response.status_code, 200)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 5)
        record.refresh_from_db()
        self.assertEqual(record.status, 'returned')

    def test_user_authentication(self):
        login_success = self.client.login(username='teststudent', password='testpassword123')
        self.assertTrue(login_success)
        response = self.client.get(reverse('my_loans'))
        self.assertEqual(response.status_code, 200)

