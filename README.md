# Campus to Career — Full-Stack Job Portal

**Campus to Career** is a modern, responsive, production-ready full-stack job portal web application designed for college students, freshers, and early-career professionals (0–3 years experience). It connects YouTube job update videos with structured job postings, company profiles, preparation guidance, and direct official application links.

---

## Key Features

- **YouTube-First Workflow**: Seamlessly attach YouTube video URLs to job listings. Embedded responsive players showcase video walk-throughs directly on job pages.
- **Advanced Job Search & Multi-Filter**: Filter jobs by keyword, hiring company, category, experience, job type, work mode (Remote/On-site/Hybrid), and location with instant pagination.
- **Original Value Content (Campus to Career Analysis)**: Add exclusive preparation guidance, resume advice, and interview stage expectations without copying boilerplate text.
- **Direct Official Links**: **Apply on Official Website →** buttons redirect users straight to employer career portals.
- **SEO & Google Indexing**: Valid JSON-LD `JobPosting` structured data on every job page, dynamic `sitemap.xml`, `robots.txt`, and canonical OpenGraph social preview tags.
- **Admin Dashboard**: Daily administrative control panel to manage jobs, companies, categories, YouTube video links, contact inbox messages, and newsletter subscribers (with CSV export).
- **Quality Checklist & Auto Slugs**: Pre-publish checklist highlights missing critical fields in real-time, while automatic slug generation ensures SEO-friendly URLs.
- **Monetization Ready**: Integrated advertisement placeholder slots (Header, homepage, between job cards, job detail sidebar, and footer) ready for Google AdSense replacement.

---

## Technology Stack

- **Backend**: Python 3.10+ / Flask 3.0
- **Database**: MySQL / SQLite fallback via SQLAlchemy ORM
- **Authentication**: Flask-Login + Werkzeug secure password hashing
- **Forms & Security**: Flask-WTF, WTForms, CSRF Protection, XSS prevention
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript (ES6)
- **Templating**: Jinja2
- **Testing**: Pytest 8.0

---

## Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 2. Clone / Setup Project
```bash
cd jobportal
```

### 3. Create & Activate Virtual Environment
```bash
# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Linux/macOS:
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Variables Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` configuration:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production-12345
DATABASE_URL=sqlite:///campus_to_career.db

# Production MySQL connection string example:
# DATABASE_URL=mysql+pymysql://username:password@localhost:3306/campustocareer

ADMIN_EMAIL=admin@campustocareer.com
ADMIN_PASSWORD=Admin@123456
```

---

## Database Seeding & Admin Credentials

Run the database seed script to initialize tables and populate sample companies (TCS, Infosys, Accenture, Wipro, Deloitte) and sample fresher job postings:

```bash
python seed.py
```

### Default Admin Credentials:
- **Login URL**: `http://127.0.0.1:5000/admin/login`
- **Email**: `admin@campustocareer.com`
- **Password**: `Admin@123456`

*(Note: Change this password immediately upon initial admin login).*

---

## Running the Application Locally

Start the local Flask development server:

```bash
python run.py
```

Open your browser and visit:
- **Public Portal**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Browse Jobs**: [http://127.0.0.1:5000/jobs](http://127.0.0.1:5000/jobs)
- **Admin Panel**: [http://127.0.0.1:5000/admin/dashboard](http://127.0.0.1:5000/admin/dashboard)
- **Sitemap**: [http://127.0.0.1:5000/sitemap.xml](http://127.0.0.1:5000/sitemap.xml)

---

## Daily Admin Workflow

1. Discover new job opportunity.
2. Log in to `/admin/login`.
3. Click **+ Add New Job**.
4. Fill in basic details, company, eligibility, and official application URL.
5. Publish job.
6. Record YouTube video explaining the job opportunity.
7. Paste YouTube video link under job editor or `/admin/youtube`.
8. The job page automatically embeds the video player!
9. Place the job web page URL in your YouTube video description.

---

## Running Tests

Execute the Pytest test suite:

```bash
pytest -v
```

Tests cover route accessibility, database models, slug generation, YouTube URL parsing, admin authorization, and job creation.

---

## Production Deployment Guide

### Deployment on Render / Railway
1. Push repository to GitHub.
2. Create a Web Service on Render / Railway connected to your repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn run:app`
5. Set environment variables in platform dashboard (`SECRET_KEY`, `DATABASE_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`).
6. Attach a MySQL database instance (e.g. Railway MySQL or Render PostgreSQL/MySQL).

### Backup & Maintenance
- Perform daily automated database backups of your MySQL instance.
- Monitor log files and view analytics via `/admin/dashboard`.
