"""
Database Seeding & Superuser Automation Script
Used locally and in Render build/start commands to ensure a functional, populated environment.
"""

import os
import django
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_project.settings")
django.setup()

from django.contrib.auth.models import User
from library.models import Category, Book, BorrowRecord, Review


def main():
    print("--- Running create_superuser.py & database seeder ---")

    # 1. Superuser Creation
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@digitallibrary.org")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")

    admin_user, created = User.objects.get_or_create(username=username, defaults={"email": email, "is_staff": True, "is_superuser": True})
    if created:
        admin_user.set_password(password)
        admin_user.first_name = "Chief"
        admin_user.last_name = "Librarian"
        admin_user.save()
        print(f"[OK] Created superuser '{username}' with password '{password}'")
    else:
        # Ensure staff & superuser flags are intact
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print(f"[INFO] Superuser '{username}' already exists.")

    # 2. Sample Member User
    student_user, s_created = User.objects.get_or_create(
        username="alex_reader",
        defaults={
            "email": "alex.reader@university.edu",
            "first_name": "Alex",
            "last_name": "Taylor",
        }
    )
    if s_created:
        student_user.set_password("student123")
        student_user.save()
        print("[OK] Created student demo account 'alex_reader' (password: 'student123')")

    # 3. Seed Categories
    categories_data = [
        {
            "name": "Computer Science & Engineering",
            "slug": "computer-science",
            "icon": "bi-cpu",
            "description": "Foundational computing systems, algorithm design, software architecture, and networking."
        },
        {
            "name": "Artificial Intelligence & Data",
            "slug": "artificial-intelligence",
            "icon": "bi-robot",
            "description": "Machine learning, neural networks, computer vision, and modern statistical modeling."
        },
        {
            "name": "Science & Mathematics",
            "slug": "science-math",
            "icon": "bi-calculator",
            "description": "Physics, pure and applied mathematics, astronomy, and chemical sciences."
        },
        {
            "name": "History & Philosophy",
            "slug": "history-philosophy",
            "icon": "bi-hourglass-split",
            "description": "World civilizations, modern history, philosophical inquiries, and human thought."
        },
        {
            "name": "Classic Literature & Fiction",
            "slug": "literature",
            "icon": "bi-book",
            "description": "Timeless literary masterpieces, prose, drama, and contemporary classics."
        },
    ]

    cat_map = {}
    for cat_info in categories_data:
        cat_obj, _ = Category.objects.get_or_create(
            name=cat_info["name"],
            defaults={
                "slug": cat_info["slug"],
                "icon": cat_info["icon"],
                "description": cat_info["description"]
            }
        )
        cat_map[cat_info["slug"]] = cat_obj

    # 4. Seed Books (if catalog is under 5 books)
    if Book.objects.count() < 5:
        sample_books = [
            {
                "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
                "author": "Robert C. Martin",
                "isbn": "978-0132350884",
                "category": cat_map["computer-science"],
                "publication_year": 2008,
                "publisher": "Prentice Hall",
                "total_copies": 6,
                "available_copies": 4,
                "cover_image_url": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=600&q=80",
                "is_featured": True,
                "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees. Clean Code helps developers write elegant, maintainable code through pragmatic principles and case studies."
            },
            {
                "title": "The Pragmatic Programmer: Your Journey To Mastery",
                "author": "David Thomas, Andrew Hunt",
                "isbn": "978-0135957059",
                "category": cat_map["computer-science"],
                "publication_year": 2019,
                "publisher": "Addison-Wesley Professional",
                "total_copies": 5,
                "available_copies": 3,
                "cover_image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=600&q=80",
                "is_featured": True,
                "description": "A classic guide examining the core of modern software development. Covers ubiquitous approaches to avoiding duplication, writing flexible software, and mastering professional craftsmanship."
            },
            {
                "title": "Artificial Intelligence: A Modern Approach",
                "author": "Stuart Russell, Peter Norvig",
                "isbn": "978-0134610993",
                "category": cat_map["artificial-intelligence"],
                "publication_year": 2020,
                "publisher": "Pearson Education",
                "total_copies": 4,
                "available_copies": 2,
                "cover_image_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80",
                "is_featured": True,
                "description": "The definitive, universally recognized university textbook introducing intelligent agents, probabilistic reasoning, machine learning, and ethics in automated systems."
            },
            {
                "title": "Designing Data-Intensive Applications",
                "author": "Martin Kleppmann",
                "isbn": "978-1449373320",
                "category": cat_map["computer-science"],
                "publication_year": 2017,
                "publisher": "O'Reilly Media",
                "total_copies": 5,
                "available_copies": 5,
                "cover_image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80",
                "is_featured": True,
                "description": "An indispensable handbook navigating the architecture, data models, replication, partitioning, and consistency models of large-scale distributed systems."
            },
            {
                "title": "Deep Learning with Python",
                "author": "François Chollet",
                "isbn": "978-1617296864",
                "category": cat_map["artificial-intelligence"],
                "publication_year": 2021,
                "publisher": "Manning Publications",
                "total_copies": 4,
                "available_copies": 3,
                "cover_image_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=600&q=80",
                "is_featured": False,
                "description": "Written by the creator of Keras, this book introduces deep learning using Python and intuitive mathematical concepts, covering computer vision, NLP, and generative AI."
            },
            {
                "title": "Sapiens: A Brief History of Humankind",
                "author": "Yuval Noah Harari",
                "isbn": "978-0062316097",
                "category": cat_map["history-philosophy"],
                "publication_year": 2015,
                "publisher": "Harper",
                "total_copies": 6,
                "available_copies": 4,
                "cover_image_url": "https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=600&q=80",
                "is_featured": True,
                "description": "From a renowned historian comes a groundbreaking narrative of humanity's creation and evolution, exploring how biology and history have defined us and enhanced our understanding of what it means to be human."
            },
            {
                "title": "A Brief History of Time",
                "author": "Stephen Hawking",
                "isbn": "978-0553380163",
                "category": cat_map["science-math"],
                "publication_year": 1998,
                "publisher": "Bantam Books",
                "total_copies": 5,
                "available_copies": 4,
                "cover_image_url": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=600&q=80",
                "is_featured": False,
                "description": "A landmark volume in science writing by one of the great minds of our time, exploring black holes, general relativity, quantum mechanics, and the origins of our cosmos."
            },
            {
                "title": "1984 (Centennial Edition)",
                "author": "George Orwell",
                "isbn": "978-0451524935",
                "category": cat_map["literature"],
                "publication_year": 1949,
                "publisher": "Signet Classic",
                "total_copies": 7,
                "available_copies": 6,
                "cover_image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
                "is_featured": False,
                "description": "The haunting dystopian masterpiece portraying the oppressive surveillance world of Oceania, Big Brother, Thought Police, and the struggle for human truth."
            }
        ]

        created_books = []
        for b_data in sample_books:
            b_obj, _ = Book.objects.get_or_create(
                isbn=b_data["isbn"],
                defaults=b_data
            )
            created_books.append(b_obj)
        print(f"[OK] Seeded {len(created_books)} catalog books.")

        # 5. Seed Demo Loan Records
        today = date.today()
        # Active Loan
        b1 = created_books[0]
        BorrowRecord.objects.get_or_create(
            book=b1,
            user=student_user,
            defaults={
                "borrow_date": today - timedelta(days=5),
                "due_date": today + timedelta(days=9),
                "status": "borrowed",
                "notes": "Research study on refactoring and software design patterns."
            }
        )

        # Overdue Loan (demonstrates late fine calculation)
        b2 = created_books[1]
        BorrowRecord.objects.get_or_create(
            book=b2,
            user=student_user,
            defaults={
                "borrow_date": today - timedelta(days=20),
                "due_date": today - timedelta(days=4),
                "status": "overdue",
                "fine_amount": Decimal("2.00"),  # 4 days * $0.50
                "notes": "Course reading for Agile Engineering."
            }
        )

        # Completed Returned Loan
        b3 = created_books[2]
        BorrowRecord.objects.get_or_create(
            book=b3,
            user=student_user,
            defaults={
                "borrow_date": today - timedelta(days=30),
                "due_date": today - timedelta(days=16),
                "return_date": today - timedelta(days=17),
                "status": "returned",
                "fine_amount": Decimal("0.00"),
                "notes": "Completed assignment on Bayesian networks."
            }
        )

        # 6. Seed Sample Reviews
        Review.objects.get_or_create(
            book=b1,
            user=student_user,
            defaults={
                "rating": 5,
                "comment": "An absolute game changer for every software engineer. The principles on naming conventions, small functions, and readability transformed how I write software."
            }
        )
        Review.objects.get_or_create(
            book=b2,
            user=student_user,
            defaults={
                "rating": 5,
                "comment": "Invaluable tips and wisdom that remain relevant no matter what framework or language you use. Highly recommended for all students!"
            }
        )
        print("[OK] Seeded sample loan records and reader reviews.")

    print("--- Database seeding complete! ---")


if __name__ == "__main__":
    main()
