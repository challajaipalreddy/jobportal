# app/admin/auto_url_job_adder.py
import re
import urllib.request
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from app.extensions import db
from app.models import Job, Company, Category
from app.utils import generate_unique_slug

def add_job_from_url_or_data(app, target_url, title=None, company_name=None, location=None, experience=None, salary=None, qualification=None, skills=None, description=None, job_type="Full-Time", work_mode="On-site"):
    """
    Parses a job URL or raw inputs and automatically creates a published live job in DB.
    """
    with app.app_context():
        # Fetch page text if URL provided and fields missing
        scraped_text = ""
        if target_url and target_url.startswith("http"):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                req = urllib.request.Request(target_url, headers=headers)
                html_bytes = urllib.request.urlopen(req, timeout=10).read()
                soup = BeautifulSoup(html_bytes, 'html.parser')
                
                # Try reading title from og:title or title tag
                if not title:
                    og_title = soup.find('meta', property='og:title') or soup.find('title')
                    if og_title:
                        title = og_title.get('content') or og_title.string

                scraped_text = soup.get_text(separator=' ')
            except Exception as err:
                print(f"URL scraping notice for {target_url}:", err)

        # Smart defaults if still missing
        if not title:
            # Infer title from URL
            clean_url_slug = target_url.rstrip('/').split('/')[-1].replace('-', ' ').replace('_', ' ').title()
            title = clean_url_slug if len(clean_url_slug) > 3 else "Software Engineer Off-Campus Hiring"

        if not company_name:
            # Infer company from title or domain
            if "Tcs" in title or "tcs" in target_url.lower():
                company_name = "TCS (Tata Consultancy Services)"
            elif "Infosys" in title or "infosys" in target_url.lower():
                company_name = "Infosys"
            elif "Accenture" in title or "accenture" in target_url.lower():
                company_name = "Accenture"
            elif "Wipro" in title or "wipro" in target_url.lower():
                company_name = "Wipro"
            elif "Cognizant" in title or "cognizant" in target_url.lower():
                company_name = "Cognizant"
            elif "Deloitte" in title or "deloitte" in target_url.lower():
                company_name = "Deloitte"
            elif "Google" in title or "google" in target_url.lower():
                company_name = "Google"
            elif "Amazon" in title or "amazon" in target_url.lower():
                company_name = "Amazon"
            else:
                # Extract second-level domain name
                try:
                    domain = target_url.split('/')[2].replace('www.', '').split('.')[0]
                    company_name = domain.capitalize() if domain else "Leading Tech Employer"
                except Exception:
                    company_name = "Leading Tech Employer"

        if not location:
            if "remote" in title.lower() or "wfh" in title.lower() or "remote" in scraped_text.lower():
                location = "Remote (Work From Home)"
                work_mode = "Remote"
            else:
                location = "Bangalore / Hyderabad / Pune / Pan India"

        if not experience:
            experience = "0–2 Years (Freshers Allowed)"

        if not qualification:
            qualification = "B.E / B.Tech / M.Tech / MCA / B.Sc / BCA"

        if not salary:
            if "intern" in title.lower() or job_type == "Internship":
                salary = "Stipend ₹20,000 – ₹35,000 / month"
            else:
                salary = "₹ 4.0 LPA – ₹ 8.5 LPA"

        if not skills:
            skills = "Java, Python, SQL, C++, Data Structures, Web Development, Aptitude"

        # Check or create Company
        comp = Company.query.filter(Company.name.ilike(f"%{company_name}%")).first()
        if not comp:
            comp_slug = generate_unique_slug(Company, company_name)
            comp = Company(
                name=company_name,
                slug=comp_slug,
                logo=f"https://ui-avatars.com/api/?name={urllib.parse.quote(company_name)}&background=0B132B&color=F97316&size=128",
                website=target_url
            )
            db.session.add(comp)
            db.session.commit()

        # Check Category
        cat = Category.query.first()
        if "intern" in title.lower():
            job_type = "Internship"
            int_cat = Category.query.filter_by(slug='internships').first()
            if int_cat:
                cat = int_cat

        job_slug = generate_unique_slug(Job, title)

        short_desc = f"{company_name} is currently hiring for {title} located at {location}. Eligible candidates with {qualification} qualification ({experience}) can apply directly on the official career portal."
        
        full_desc = description or f"### {company_name} - {title}\n\n{company_name} has officially announced off-campus hiring for {title}.\n\n#### Job Overview:\n- **Company**: {company_name}\n- **Role**: {title}\n- **Location**: {location}\n- **Experience**: {experience}\n- **Qualifications**: {qualification}\n- **Salary/CTC**: {salary}\n- **Key Skills**: {skills}\n\n#### Responsibilities:\n1. Design, develop, and maintain software applications and engineering solutions.\n2. Write clean, efficient, and well-tested code.\n3. Collaborate with cross-functional teams and senior engineers.\n\n#### How to Apply:\nClick the Apply button below to submit your application directly on the official {company_name} career portal."

        job = Job(
            title=title,
            slug=job_slug,
            company_id=comp.id,
            company_logo=comp.logo,
            category_id=cat.id if cat else None,
            job_type=job_type,
            location=location,
            work_mode=work_mode,
            qualification=qualification,
            experience=experience,
            skills=skills,
            salary=salary,
            short_description=short_desc,
            description=full_desc,
            responsibilities="1. Work on software engineering tasks & modules.\n2. Participate in code reviews, testing, and debugging.\n3. Collaborate with team leads and peer engineers.",
            eligibility=f"Degree: {qualification}\nExperience: {experience}\nAcademic Cutoff: 60% or 6.0 CGPA throughout 10th, 12th & Graduation.",
            application_url=target_url,
            source_url=target_url,
            application_deadline=datetime.utcnow().date() + timedelta(days=30),
            campus_analysis=f"Verified high-priority career drive at {company_name} for {title}. Great opportunity for freshers to kickstart their career.",
            who_can_apply=f"Graduates with {qualification} qualification ({experience}).",
            resume_tips=f"1. Highlight projects built using {skills}.\n2. Include live GitHub repository links and project URLs.\n3. Detail individual technical contributions.",
            interview_tips="Round 1: Online Technical & Aptitude Test.\nRound 2: Technical Interview & Live Coding.\nRound 3: HR Discussion.",
            status='Active',
            featured=True
        )

        db.session.add(job)
        db.session.commit()

        live_url = f"https://jobportal-3-123t.onrender.com/jobs/{job.slug}"
        print(f"SUCCESSFULLY_ADDED_JOB: {job.title} | LIVE_URL: {live_url}")
        return {
            'success': True,
            'job_id': job.id,
            'title': job.title,
            'slug': job.slug,
            'company': company_name,
            'live_url': live_url
        }
