# LibroSphere — Full-Stack Digital Library Management System

A production-ready full-stack web application developed using **Python**, **Django 6**, **SQLite**, **Bootstrap 5**, and **Vanilla JavaScript (ES6+)**, configured for cloud deployment on **Render**.

---

## 1. Project Overview & Problem Statement

### Real-World Problem
Traditional library tracking and catalog discovery often suffer from scattered records, missing real-time availability tracking, manual loan return computations, and a lack of dynamic due date and late fee warnings. Students frequently struggle to discover relevant books, while library administrators must manage borrowing workflows manually.

### Proposed Solution
**LibroSphere** provides an intuitive, centralized digital platform where:
- **Readers & Students** can explore book collections across diverse academic disciplines, instantly filter by availability or category without page reloads, borrow titles with automatic due-date tracking, estimate overdue fines dynamically, and post ratings/reviews.
- **Librarians & Staff** can manage the catalog (full CRUD operations), oversee library-wide active and overdue loans, process book returns with one click, and track inventory metrics.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.3, Bootstrap Icons 1.11.3 |
| **Backend** | Python 3.11+ & Django 6.x (MVT Architecture) |
| **Database** | SQLite (`db.sqlite3`) via Django ORM |
| **Static Files** | WhiteNoise (`whitenoise.middleware.WhiteNoiseMiddleware`) |
| **WSGI Server** | Gunicorn |
| **Deployment** | Render (Infrastructure as Code via `render.yaml`) |
| **Version Control** | Git & GitHub |

---

## 3. Database Architecture (Django Models & ORM)

The application features **4 related models** with multiple `ForeignKey` relationships:

1. **`Category`**:
   - Fields: `name`, `slug`, `icon`, `description`, `created_at`.
   - Relationships: One-to-Many with `Book`.

2. **`Book`**:
   - Fields: `title`, `author`, `isbn`, `category` (FK), `description`, `publication_year`, `publisher`, `total_copies`, `available_copies`, `cover_image_url`, `is_featured`, `created_at`.
   - Relationships: Many-to-One with `Category`; One-to-Many with `BorrowRecord` and `Review`.
   - Validation: `available_copies <= total_copies`, valid publication years.

3. **`BorrowRecord`**:
   - Fields: `book` (FK), `user` (FK), `borrow_date`, `due_date`, `return_date`, `status` (`borrowed`, `returned`, `overdue`), `fine_amount`, `notes`, `created_at`.
   - Logic: Automated overdue detection, daily late fee calculation ($0.50/day).

4. **`Review`**:
   - Fields: `book` (FK), `user` (FK), `rating` (1 to 5 stars), `comment`, `created_at`.
   - Constraint: `unique_together = ('book', 'user')` (one review per member per book).

---

## 4. Key Features & Requirements Compliance

### Full CRUD Operations
- **Create**: Add new books (`BookForm`), create categories (`CategoryForm`), submit borrow requests, submit ratings & reviews (`ReviewForm`), register user accounts (`UserRegisterForm`).
- **Read**: Dynamic book catalog with live stats, book detail pages with stock & reviews, user "My Loans" dashboard, librarian "Manage Loans" portal.
- **Update**: Edit book details and inventory levels, process returns (restocks copies and calculates fines), renew active loans (+7 days extension).
- **Delete**: Remove books with confirmation warnings and review deletion.

### Server-Side Validation & Security
- ISBN format verification (10 or 13 digits).
- Copy count validation (`available_copies` cannot exceed `total_copies`).
- Duplicate active loan prevention (users cannot borrow the same book twice simultaneously).
- Out-of-stock prevention (cannot checkout when available copies = 0).
- CSRF protection enabled on every POST form (`{% csrf_token %}`).
- Role-based permissions (`@login_required`, `@user_passes_test(is_librarian)`).

### Interactive JavaScript Features (ES6+)
1. **Live Instant Search & Category Filter**: Real-time client-side book filtering as the user types without refreshing the page, accompanied by dynamic count updates and an empty-state alert.
2. **Dynamic Loan Due Date & Late Fee Simulator Modal**: Interactive modal that calculates the exact calendar due date based on chosen loan duration (7, 14, 21, 30 days) and provides an interactive slider demonstrating estimated late fees.
3. **Interactive Star Rating & Character Counter**: Real-time character counter badge for reviews and descriptions that dynamically changes color (green &rarr; yellow &rarr; red), and interactive rating descriptions.
4. **Auto-Dismiss Alerts**: Bootstrap alerts that smoothly fade out after 5 seconds.

---

## 5. Local Setup Instructions

### 1. Prerequisites
- Python 3.11+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations & Database Seeding
```bash
python manage.py makemigrations
python manage.py migrate
python create_superuser.py
```
*The seeding script automatically registers default categories, 8 books with cover images, sample loans, and pre-configured accounts.*

### 4. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 6. Pre-Configured Demo Accounts

| Role | Username | Password | Notes |
|---|---|---|---|
| **Librarian / Admin** | `admin` | `admin123` | Full access: CRUD books, manage all loans, Django Admin (`/admin/`) |
| **Student / Reader** | `alex_reader` | `student123` | Member access: borrow books, renew, view personal loans, write reviews |

*New members can also register directly at `/register/`.*

---

## 7. Render Cloud Deployment Guide

This project is configured for deployment to **Render** via `render.yaml`, `requirements.txt`, and `create_superuser.py`.

### Step-by-Step Deployment:
1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of full-stack Digital Library"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

2. **Create Web Service on Render**:
   - Log in to [Render Dashboard](https://dashboard.render.com/).
   - Click **New +** &rarr; **Blueprint** (or **Web Service**).
   - Connect your GitHub repository.
   - If using **Web Service** manually:
     - **Runtime**: `Python`
     - **Build Command**:
       ```bash
       pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python create_superuser.py
       ```
     - **Start Command**:
       ```bash
       python manage.py migrate && python create_superuser.py && gunicorn library_project.wsgi:application
       ```

3. **Set Environment Variables on Render**:
   - `PYTHON_VERSION`: `3.11.0`
   - `RENDER`: `True`
   - `SECRET_KEY`: *[Generate or provide any secret key]*

4. **Deploy**:
   - Click **Deploy Web Service**.
   - Render will build the environment, collect static assets via WhiteNoise, apply SQLite migrations, and seed initial demo data via `create_superuser.py`.
   - Access your live deployment at `https://<your-service-name>.onrender.com`.

---

## 8. Project Structure

```
├── manage.py
├── requirements.txt
├── render.yaml
├── create_superuser.py
├── .gitignore
├── README.md
├── db.sqlite3
├── library_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── library/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── urls.py
    ├── views.py
    ├── migrations/
    │   └── 0001_initial.py
    ├── static/
    │   └── library/
    │       ├── css/
    │       │   └── style.css
    │       └── js/
    │           └── main.js
    └── templates/
        └── library/
            ├── base.html
            ├── book_list.html
            ├── book_detail.html
            ├── book_form.html
            ├── book_confirm_delete.html
            ├── my_loans.html
            ├── manage_loans.html
            ├── category_form.html
            ├── login.html
            └── register.html
```
