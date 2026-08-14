import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Company, Category, Job, DailyJobUpdate, CareerTip, Subscriber, ContactMessage, SiteSetting
from app.utils import generate_unique_slug

def seed_database(app_instance=None):
    if app_instance is None:
        from app import create_app
        app_instance = create_app('development')

    with app_instance.app_context():
        from app.extensions import db
        print("Recreating database tables with updated schema...")
        db.create_all()


        # 1. Create Default Admin User
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@campustocareer.com')
        admin_pass = os.environ.get('ADMIN_PASSWORD', 'Admin@123456')
        
        admin = User(username='admin', email=admin_email, is_admin=True)
        admin.set_password(admin_pass)
        db.session.add(admin)
        print(f"Created Admin account: {admin_email}")

        # 2. Create Sample Companies
        companies_data = [
            {
                'name': 'TCS (Tata Consultancy Services)',
                'slug': 'tcs',
                'logo': 'https://upload.wikimedia.org/wikipedia/commons/b/b1/Tata_Consultancy_Services_Logo.svg',
                'website': 'https://www.tcs.com',
                'description': 'TCS is a global leader in IT services, consulting, and business solutions.'
            },
            {
                'name': 'Infosys',
                'slug': 'infosys',
                'logo': 'https://upload.wikimedia.org/wikipedia/commons/9/95/Infosys_logo.svg',
                'website': 'https://www.infosys.com',
                'description': 'Infosys is a global leader in next-generation digital services and consulting.'
            },
            {
                'name': 'Accenture',
                'slug': 'accenture',
                'logo': 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Accenture.svg',
                'website': 'https://www.accenture.com',
                'description': 'Accenture is a leading global professional services company.'
            },
            {
                'name': 'Wipro',
                'slug': 'wipro',
                'logo': 'https://upload.wikimedia.org/wikipedia/commons/a/a0/Wipro_Primary_Logo_Color_RGB.svg',
                'website': 'https://www.wipro.com',
                'description': 'Wipro Limited is a leading global technology services company.'
            },
            {
                'name': 'Deloitte',
                'slug': 'deloitte',
                'logo': 'https://upload.wikimedia.org/wikipedia/commons/5/56/Deloitte.svg',
                'website': 'https://www2.deloitte.com',
                'description': 'Deloitte provides audit, consulting, tax and risk advisory services.'
            }
        ]

        companies_dict = {}
        for cdata in companies_data:
            comp = Company(**cdata)
            db.session.add(comp)
            companies_dict[cdata['slug']] = comp
        db.session.commit()
        print("Created sample companies.")

        # 3. Create Categories
        categories_data = [
            {'name': 'Software Development', 'slug': 'software-development', 'icon': 'bi-code-slash', 'description': 'Full-stack, frontend, backend & software engineering roles.'},
            {'name': 'Data Analytics', 'slug': 'data-analytics', 'icon': 'bi-graph-up', 'description': 'Data analysis, SQL, BI reporting & insight roles.'},
            {'name': 'Data Science', 'slug': 'data-science', 'icon': 'bi-cpu', 'description': 'Machine learning, AI & predictive modeling jobs.'},
            {'name': 'Testing', 'slug': 'testing', 'icon': 'bi-bug', 'description': 'QA engineering, automation testing & manual testing.'},
            {'name': 'Cloud', 'slug': 'cloud', 'icon': 'bi-cloud', 'description': 'AWS, Azure, GCP infrastructure & cloud administration.'},
            {'name': 'DevOps', 'slug': 'devops', 'icon': 'bi-gear-wide-connected', 'description': 'CI/CD pipelines, Docker, Kubernetes & infrastructure automation.'},
            {'name': 'Cyber Security', 'slug': 'cyber-security', 'icon': 'bi-shield-lock', 'description': 'Network security, SOC analysis & ethical hacking.'},
            {'name': 'UI/UX', 'slug': 'ui-ux', 'icon': 'bi-palette', 'description': 'User interface design, Figma wireframing & UX research.'},
            {'name': 'Internships', 'slug': 'internships', 'icon': 'bi-mortarboard', 'description': 'Paid & stipend internships for college students.'},
            {'name': 'Government Jobs', 'slug': 'government-jobs', 'icon': 'bi-building-check', 'description': 'Public sector & government job notifications.'}
        ]

        categories_dict = {}
        for catdata in categories_data:
            cat = Category(**catdata)
            db.session.add(cat)
            categories_dict[catdata['slug']] = cat
        db.session.commit()
        print("Created sample categories.")

        # 4. Create Daily Job Video Group Update
        today_date = datetime.utcnow().date()
        daily_update = DailyJobUpdate(
            title="Today's Latest Jobs — 14 August 2026",
            slug="14-august-2026",
            update_date=today_date,
            youtube_video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            youtube_video_id="dQw4w9WgXcQ",
            youtube_description="""TODAY'S TOP JOBS (14 AUGUST 2026):

1. TCS Software Engineer – Freshers
https://campustocareer.in/jobs/tcs-software-engineer-freshers-2026-batch

2. Infosys Systems Engineer Off-Campus
https://campustocareer.in/jobs/infosys-systems-engineer-off-campus-hiring-drive

3. Accenture Associate Software Engineer
https://campustocareer.in/jobs/accenture-associate-software-engineer-ase

4. Deloitte Data Analyst Intern
https://campustocareer.in/jobs/deloitte-data-analyst-intern-summer-2026

Subscribe to Campus to Career for daily hiring updates!"""
        )
        db.session.add(daily_update)
        db.session.commit()

        # 5. Create Sample Jobs
        sample_jobs = [
            {
                'title': 'TCS Software Engineer – Freshers 2026 Batch',
                'slug': 'tcs-software-engineer-freshers-2026-batch',
                'company_id': companies_dict['tcs'].id,
                'category_id': categories_dict['software-development'].id,
                'daily_update_id': daily_update.id,
                'job_type': 'Full-Time',
                'work_mode': 'On-site',
                'location': 'Pan India (Bangalore, Pune, Hyderabad, Chennai, Noida)',
                'qualification': 'B.Tech / B.E / M.Tech / MCA / M.Sc',
                'experience': '0–2 Years (Freshers Allowed)',
                'skills': 'Java, Python, C++, Data Structures, SQL, OOPS',
                'eligibility': 'Candidates graduating in 2024, 2025, or 2026 with 60% or 6.0 CGPA throughout academics without active backlogs.',
                'short_description': 'TCS is hiring freshers for Software Engineer roles across multiple locations in India.',
                'description': """TCS has announced its nationwide fresher recruitment drive for Software Engineer roles.

Key Highlights:
- Structured initial training at TCS ILP (Initial Learning Program).
- Work on cutting-edge enterprise projects across Banking, Healthcare, and Cloud.
- Fast-track career growth through internal assessments.""",
                'responsibilities': """1. Write clean, efficient code in Java, C++, or Python.
2. Collaborate with cross-functional software development teams.
3. Participate in code reviews and bug fixes.""",
                'salary': '₹ 3.36 LPA – ₹ 7.00 LPA',
                'application_url': 'https://www.tcs.com/careers',
                'source_url': 'https://nextstep.tcs.com',
                'application_deadline': (datetime.utcnow() + timedelta(days=15)).date(),
                'status': 'Active',
                'featured': True,
                'youtube_video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'youtube_video_id': 'dQw4w9WgXcQ',
                'youtube_title': 'TCS Fresher Hiring 2026 | Eligibility, Salary & Apply Process',
                'youtube_thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                'campus_analysis': 'Highly recommended for fresh engineering and MCA graduates looking for strong brand value, job stability, and tech training.',
                'who_can_apply': '2024, 2025, and 2026 passouts in CSE, IT, ECE, EEE, and MCA degrees.',
                'resume_tips': 'Highlight academic projects and DSA skills on page 1 of your resume.',
                'interview_tips': 'Round 1: Online Aptitude + Coding Assessment. Round 2: Technical Interview. Round 3: HR Interview.'
            },
            {
                'title': 'Infosys Systems Engineer Off-Campus Hiring Drive',
                'slug': 'infosys-systems-engineer-off-campus-hiring-drive',
                'company_id': companies_dict['infosys'].id,
                'category_id': categories_dict['software-development'].id,
                'daily_update_id': daily_update.id,
                'job_type': 'Full-Time',
                'work_mode': 'Hybrid',
                'location': 'Bangalore, Mysore, Pune, Hyderabad',
                'qualification': 'B.E / B.Tech / M.E / M.Tech / MCA',
                'experience': '0–1 Years',
                'skills': 'C#, Python, Java, Database Management',
                'eligibility': 'Aggregate of 60% or above in 10th, 12th, and Graduation.',
                'short_description': 'Infosys is inviting applications for Systems Engineer roles across India.',
                'description': 'Infosys Systems Engineer role offers entry-level IT professionals an opportunity to learn modern software engineering frameworks.',
                'responsibilities': 'Develop and maintain software components according to client requirements.',
                'salary': '₹ 3.60 LPA',
                'application_url': 'https://www.infosys.com/careers/freshers.html',
                'source_url': 'https://www.infosys.com/careers',
                'application_deadline': (datetime.utcnow() + timedelta(days=10)).date(),
                'status': 'Active',
                'featured': True,
                'youtube_video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'youtube_video_id': 'dQw4w9WgXcQ',
                'youtube_title': 'Infosys Off Campus Hiring 2026 | Full Registration Guide',
                'youtube_thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                'campus_analysis': 'Infosys Mysore training is world-renowned. Great starting point.',
                'who_can_apply': 'Engineering & MCA passouts with foundational programming knowledge.',
                'resume_tips': 'Keep resume clean and mention basic Git and SQL experience.',
                'interview_tips': 'Prepare pseudo-code writing and basics of SQL queries.'
            },
            {
                'title': 'Accenture Associate Software Engineer (ASE)',
                'slug': 'accenture-associate-software-engineer-ase',
                'company_id': companies_dict['accenture'].id,
                'category_id': categories_dict['software-development'].id,
                'daily_update_id': daily_update.id,
                'job_type': 'Full-Time',
                'work_mode': 'On-site',
                'location': 'Gurgaon, Mumbai, Bangalore, Kolkata',
                'qualification': 'All Streams Graduate (B.Tech / BCA / B.Sc)',
                'experience': '0–2 Years',
                'skills': 'Cloud Basics, JavaScript, SQL, Logic Building',
                'eligibility': 'Full-time graduation degree with no active backlogs.',
                'short_description': 'Accenture is hiring Associate Software Engineers across India.',
                'description': 'Work with leading cloud applications and enterprise architecture solutions.',
                'responsibilities': 'Build cloud-native applications and client integrations.',
                'salary': '₹ 4.50 LPA',
                'application_url': 'https://www.accenture.com/in-en/careers',
                'source_url': 'https://accenture.com/careers',
                'application_deadline': (datetime.utcnow() + timedelta(days=7)).date(),
                'status': 'Active',
                'featured': False,
                'campus_analysis': 'Higher starting package compared to standard entry roles.',
                'who_can_apply': 'Graduates across B.Tech, BCA, and B.Sc Computer Science streams.',
                'resume_tips': 'Highlight problem-solving capability and cloud fundamentals.',
                'interview_tips': 'Online Cognitive & Technical Assessment followed by Communication test.'
            },
            {
                'title': 'Deloitte Data Analyst Intern (Summer 2026)',
                'slug': 'deloitte-data-analyst-intern-summer-2026',
                'company_id': companies_dict['deloitte'].id,
                'category_id': categories_dict['internships'].id,
                'daily_update_id': daily_update.id,
                'job_type': 'Internship',
                'work_mode': 'Remote',
                'location': 'Remote / Work From Home',
                'qualification': 'B.Tech / B.Sc / BCA / MBA Students',
                'experience': 'Internship / Student',
                'skills': 'Excel, Power BI, SQL, Python, Data Visualization',
                'eligibility': 'Currently pursuing graduation or post-graduation with analytical skills.',
                'short_description': 'Deloitte India is offering remote 6-month Data Analytics Internships.',
                'description': 'Gain hands-on experience in business intelligence and reporting dashboards.',
                'responsibilities': 'Clean dataset inputs, build Power BI dashboards, and draft reports.',
                'salary': 'Stipend: ₹ 30,000 / Month (PPO Possible)',
                'application_url': 'https://www2.deloitte.com/ui/en/careers/students.html',
                'source_url': 'https://deloitte.com/careers',
                'application_deadline': (datetime.utcnow() + timedelta(days=5)).date(),
                'status': 'Active',
                'featured': True,
                'youtube_video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'youtube_video_id': 'dQw4w9WgXcQ',
                'youtube_title': 'Deloitte Remote Data Analyst Internship 2026 | Stipend ₹30k',
                'youtube_thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                'campus_analysis': 'Earn high stipend while gaining Big 4 consulting experience.',
                'who_can_apply': 'Pre-final and final year students looking for 6-month internship.',
                'resume_tips': 'Include links to Power BI dashboards or Kaggle projects.',
                'interview_tips': 'Expect SQL query tests (JOINs, GROUP BY) and analytical case interview.'
            }
        ]

        for jdata in sample_jobs:
            job = Job(**jdata)
            db.session.add(job)
            
        db.session.commit()
        print("Created sample job postings.")

        # 6. Create Sample Career Tips
        tips_data = [
            {
                'title': 'How to Crack Service-Based MNC Written & Aptitude Tests (TCS, Infosys, Wipro)',
                'slug': 'how-to-crack-mnc-written-aptitude-tests',
                'category': 'Placement Preparation',
                'summary': 'A practical step-by-step roadmap to master quantitative aptitude, logical reasoning, and coding sections in campus placement exams.',
                'content': """Campus placement tests for service-based IT giants (like TCS NQT, Infosys System Engineer, Wipro NTH) follow a structured pattern. Here is how to prepare:

1. Quantitative Aptitude: Focus on Percentages, Profit & Loss, Time & Work, Speed Distance, and Number Systems. Practice 20 questions daily under timed constraints.
2. Logical Reasoning: Master Blood Relations, Syllogisms, Coding-Decoding, and Seating Arrangements.
3. Coding Section: Brush up basic Data Structures (Arrays, Strings, HashMaps) in C++, Java, or Python. Learn standard pattern printing and string manipulation.

Pro Tip: Accuracy matters more than speed in adaptive tests. Attempt foundational questions carefully before moving to complex ones."""
            },
            {
                'title': 'Top 10 Resume Mistakes Freshers Must Avoid in 2026',
                'slug': 'top-10-resume-mistakes-freshers-avoid',
                'category': 'Resume Building',
                'summary': 'Avoid common resume blunders that get fresh graduate resumes rejected by ATS software and HR recruiters.',
                'content': """Your resume is your first impression. Avoid these critical mistakes:

- Multi-page Resumes: Freshers should strictly keep resumes to a single page.
- Generic Project Descriptions: Don't just write "Library Management System". Specify technologies used (Python, MySQL), your role, and key outcomes.
- Missing GitHub/LinkedIn Links: Include hyperlinked URLs to your verified projects and professional profile.
- Spelling & Formatting Errors: Maintain consistent font sizes and proofread thoroughly."""
            }
        ]

        for tdata in tips_data:
            tip = CareerTip(**tdata)
            db.session.add(tip)
        db.session.commit()
        print("Created sample career tips.")

        # 7. Create Sample Subscriber & Message
        sub = Subscriber(email='student1@example.com')
        db.session.add(sub)
        
        msg = ContactMessage(
            name='Rahul Sharma',
            email='rahul.sharma@example.com',
            subject='Inquiry about TCS Drive Eligibility',
            message='Hello team, is the TCS Software Engineer drive open for 2026 MCA passouts as well?'
        )
        db.session.add(msg)

        # 8. Site Settings
        setting = SiteSetting(key='announcement_banner', value='🔥 2026 Off-Campus Placement Drives & Internships Active Now!')
        db.session.add(setting)

        db.session.commit()
        print("Created subscriber, contact message & site settings.")

        print("\n=== UPDATED DATABASE SEEDING COMPLETED SUCCESSFULLY ===")
        print(f"Admin Email: {admin_email} | Password: {admin_pass}")

if __name__ == '__main__':
    seed_database()
