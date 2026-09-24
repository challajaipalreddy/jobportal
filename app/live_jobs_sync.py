# app/live_jobs_sync.py
from datetime import datetime, timedelta

COMMUNITY_JOBS = [
    {
        'company_name': 'Sutherland',
        'company_logo': 'https://upload.wikimedia.org/wikipedia/commons/e/ec/Sutherland_Global_Services_logo.svg',
        'company_website': 'https://www.sutherlandglobal.com',
        'title': "Sutherland New Campus Associates Hiring – FY'26",
        'category_name': 'Off-Campus Drives',
        'job_type': 'Full-Time',
        'work_mode': 'Hybrid',
        'location': 'Chennai / Hyderabad / Bengaluru / Pan India',
        'experience': '0–1 Year (2024, 2025 & 2026 Batch Freshers)',
        'qualification': 'B.Tech / B.E / BCA / B.Sc / B.Com / Any Graduate',
        'salary': '₹ 3.0 LPA – ₹ 4.5 LPA',
        'skills': 'Communication Skills, Customer Engagement, Problem Solving, Analytical Ability, MS Office, IT Basics',
        'application_url': 'https://jobs.smartrecruiters.com/oneclick-ui/company/Sutherland/publication/819e73fb-c999-4f9d-9519-87b604afbc88?dcr_ci=Sutherland',
        'short_desc': 'Sutherland is hiring fresh graduates for New Campus Associates FY26. Open for 2024, 2025, and 2026 passout batches with zero backlogs.',
        'description': """### Sutherland New Campus Associates Hiring FY'26 Drive

Sutherland has officially opened off-campus hiring registrations for **New Campus Associates – FY'26**. This drive is tailored for freshers aiming to start their corporate career in customer technology, business operations, and process consulting.

#### Key Highlights:
- **Company**: Sutherland Global Services
- **Designation**: New Campus Associate - FY'26
- **Batch Eligible**: 2024, 2025 & 2026 Passouts
- **Job Location**: Chennai, Hyderabad, Bengaluru (Pan India)
- **Salary CTC**: ₹ 3.0 LPA – ₹ 4.5 LPA
- **Work Mode**: Hybrid / Work from Office

#### Responsibilities:
1. Handle technology-assisted customer operations and business support workflows.
2. Resolve user queries efficiently with high customer satisfaction ratings.
3. Collaborate with cross-functional service teams and maintain operational metrics.
4. Follow established security and data governance standards.

#### Eligibility Criteria:
- Any Graduate (B.Tech, B.E, B.Sc, BCA, B.Com, BBA).
- No active backlogs at the time of joining.
- Excellent verbal and written English communication skills.
- Willingness to work in flexible 24/7 shifts including rotational weekends.""",
        'responsibilities': "1. Deliver first-call resolution and support for business stakeholders.\n2. Maintain documentation and follow incident management protocols.\n3. Participate in ongoing corporate process and product training.",
        'eligibility': "Graduation: Any Degree (B.E / B.Tech / BCA / B.Sc / B.Com / BBA)\nBatches: 2024, 2025, and 2026 graduates\nCutoff: 55% or above throughout academics",
        'campus_analysis': "Sutherland provides structured onboarding, great career acceleration, and recognized corporate learning for freshers across India.",
        'who_can_apply': "Fresh graduates and final-year students seeking their first professional full-time role with strong communication abilities.",
        'resume_tips': "Emphasize verbal communication, English fluency certifications, internship experience, and customer-handling projects.",
        'interview_tips': "Round 1: Online English & Communication Assessment (Versant/Audio test).\nRound 2: Technical/Operational Discussion.\nRound 3: HR Final Discussion."
    },
    {
        'company_name': 'Capgemini',
        'company_logo': 'https://upload.wikimedia.org/wikipedia/commons/9/9d/Capgemini_201x_logo.svg',
        'company_website': 'https://www.capgemini.com',
        'title': 'Capgemini Java Developer Hiring (Spring Boot & Microservices)',
        'category_name': 'Software Development',
        'job_type': 'Full-Time',
        'work_mode': 'Hybrid',
        'location': 'Mumbai / Hyderabad / Bengaluru / Pune',
        'experience': '0–5 Years (Freshers & Experienced)',
        'qualification': 'B.E / B.Tech / M.E / M.Tech / MCA / M.Sc',
        'salary': '₹ 4.5 LPA – ₹ 9.0 LPA',
        'skills': 'Core Java, Spring Boot, Spring MVC, Hibernate/JPA, Microservices, REST APIs, Docker, Git, SQL',
        'application_url': 'https://www.naukri.com/job-listings-java-developer-capgemini-technology-services-india-limited-mumbai-hyderabad-bengaluru-0-to-5-years-210926922397',
        'short_desc': 'Capgemini is hiring Java Developers with 0 to 5 years experience in Spring Boot, REST APIs, and Microservices across Mumbai, Hyderabad, Bengaluru, and Pune.',
        'description': """### Capgemini Java Developer Hiring 2026

Capgemini Technology Services India is actively recruiting **Java Developers** across India. This role is ideal for software engineers with hands-on proficiency in Core Java, Spring Boot, and modern cloud microservices architectures.

#### Role Overview:
- **Organization**: Capgemini Technology Services
- **Job Role**: Java Software Developer
- **Locations**: Mumbai, Hyderabad, Bengaluru, Pune
- **Experience**: 0–5 Years
- **Salary / CTC**: ₹ 4.5 LPA – ₹ 9.0 LPA (commensurate with skills)

#### Technical Skill Requirements:
- **Core Languages**: Java 8 / 11 / 17, Object-Oriented Design, Collections framework, Multithreading.
- **Frameworks**: Spring Boot, Spring MVC, Hibernate / JPA.
- **Web Services**: RESTful API design, JSON, Microservices architecture.
- **Databases**: PostgreSQL, MySQL, Oracle SQL.
- **DevOps Tools**: Git, Maven, Jenkins, Docker, CI/CD pipelines.

#### Responsibilities:
1. Design, build, and deploy enterprise-grade Java web applications.
2. Develop scalable REST APIs and integrate backend microservices.
3. Perform unit testing with JUnit / Mockito and resolve production defects.
4. Collaborate with Agile sprint teams, technical leads, and DevOps engineers.""",
        'responsibilities': "1. Write clean, maintainable, and high-performance Java code.\n2. Build and maintain robust microservices using Spring Boot.\n3. Conduct unit testing, peer code reviews, and API documentation.",
        'eligibility': "Education: B.E / B.Tech / MCA / M.Tech in CS/IT or related branches\nExperience: 0 to 5 years hands-on Java development\nBacklogs: No active backlogs",
        'campus_analysis': "Capgemini offers tier-1 IT consulting experience, global client exposure, and structured tech career progression in enterprise software.",
        'who_can_apply': "Aspiring Java engineers, freshers with strong Spring Boot personal projects, and experienced developers seeking MNC growth.",
        'resume_tips': "Highlight personal Java/Spring Boot project repositories with live GitHub links and API documentation.",
        'interview_tips': "Round 1: Online Technical MCQ & Coding Test.\nRound 2: Technical Interview (OOPs, Collections, Multithreading, Spring Boot, SQL).\nRound 3: Managerial & HR round."
    },
    {
        'company_name': 'Red Hat',
        'company_logo': 'https://upload.wikimedia.org/wikipedia/commons/d/d8/Red_Hat_logo.svg',
        'company_website': 'https://www.redhat.com',
        'title': 'Red Hat Business / Data Analyst – Training & Certification',
        'category_name': 'Data Analytics',
        'job_type': 'Full-Time',
        'work_mode': 'Hybrid',
        'location': 'Bengaluru (Bangalore), Karnataka',
        'experience': '1–4 Years (Early Career / Experienced)',
        'qualification': "Bachelor's or Master's degree in Data Science, Computer Science, Statistics, or Business",
        'salary': '₹ 8.0 LPA – ₹ 14.0 LPA',
        'skills': 'SQL, Python, Data Analytics, Tableau, Power BI, Machine Learning, Business Intelligence, Data Modeling',
        'application_url': 'https://redhat.wd5.myworkdayjobs.com/en-US/jobs/details/Business-Data-Analyst---Training---Certification_R-058905-2?a=c4f78be1a8f14da0ab49ce1162348a5e',
        'short_desc': 'Red Hat is hiring a Business / Data Analyst for its Training & Certification group in Bengaluru. Work with Python, SQL, and data models to drive customer insights.',
        'description': """### Red Hat Business / Data Analyst – Training & Certification (Job ID: R-058905)

Red Hat, the world's leading provider of enterprise open-source solutions, is seeking a **Business / Data Analyst** to join the Red Hat Learning Subscription (RHLS) Engagement Team in Bengaluru.

#### Role Mission:
Drive customer subscription engagement and post-sale consumption through sophisticated data analytics, predictive modeling, and executive KPI reporting.

#### Core Responsibilities:
1. Aggregate and analyze complex customer engagement datasets across multiple internal data lakes.
2. Build automated BI dashboards in Tableau / Power BI for regional sales leads and leadership.
3. Utilize Python and SQL to build predictive retention and consumption models.
4. Translate data trends into actionable recommendations that increase customer learning outcomes.

#### Required Skills & Qualifications:
- Bachelor's or Master's in Computer Science, Data Analytics, Statistics, or related discipline.
- Strong proficiency in SQL writing complex queries, Window functions, and JOIN aggregations.
- Hands-on data manipulation in Python (pandas, numpy, scikit-learn).
- Proven experience with BI visualization tools (Tableau, Power BI, or Looker).
- Excellent stakeholder presentation and data storytelling skills.""",
        'responsibilities': "1. Build and maintain automated analytical models and executive dashboards.\n2. Uncover customer engagement trends to maximize subscription value.\n3. Partner with global data teams to ensure data governance and integrity.",
        'eligibility': "Degree: Bachelor's / Master's in Computer Science, Data Science, Math, or Business\nExperience: 1–4 years in Data Analytics or BI\nLocation: Bengaluru (Hybrid)",
        'campus_analysis': "Red Hat offers elite open-source culture, competitive compensation, and high-impact data analytics exposure on a global scale.",
        'who_can_apply': "Data analysts, business intelligence specialists, and data engineers with strong SQL and Python problem-solving capabilities.",
        'resume_tips': "Quantify data outcomes (e.g., 'Constructed SQL pipeline tracking $10M+ in recurring subscription revenue').",
        'interview_tips': "Round 1: SQL & Python Technical Screening.\nRound 2: Case Study & Dashboard Design Challenge.\nRound 3: Stakeholder Interaction & Behavioral Discussion."
    }
]

def sync_live_jobs(app, db, Job, Company, Category, generate_unique_slug):
    """Guarantees community jobs are inserted into live DB on startup."""
    with app.app_context():
        for item in COMMUNITY_JOBS:
            try:
                comp = Company.query.filter(Company.name.ilike(f"%{item['company_name']}%")).first()
                if not comp:
                    comp_slug = generate_unique_slug(Company, item['company_name'])
                    comp = Company(
                        name=item['company_name'],
                        slug=comp_slug,
                        logo=item['company_logo'],
                        website=item['company_website']
                    )
                    db.session.add(comp)
                    db.session.commit()

                cat = Category.query.filter(Category.name.ilike(f"%{item['category_name']}%")).first()
                if not cat:
                    cat = Category.query.first()

                existing = Job.query.filter(Job.title.ilike(f"%{item['title']}%")).first()
                if not existing:
                    job_slug = generate_unique_slug(Job, item['title'])
                    job = Job(
                        title=item['title'],
                        slug=job_slug,
                        company_id=comp.id,
                        company_logo=item['company_logo'],
                        category_id=cat.id if cat else None,
                        job_type=item['job_type'],
                        location=item['location'],
                        work_mode=item['work_mode'],
                        qualification=item['qualification'],
                        experience=item['experience'],
                        skills=item['skills'],
                        salary=item['salary'],
                        short_description=item['short_desc'],
                        description=item['description'],
                        responsibilities=item['responsibilities'],
                        eligibility=item['eligibility'],
                        application_url=item['application_url'],
                        source_url=item['application_url'],
                        application_deadline=datetime.utcnow().date() + timedelta(days=25),
                        campus_analysis=item['campus_analysis'],
                        who_can_apply=item['who_can_apply'],
                        resume_tips=item['resume_tips'],
                        interview_tips=item['interview_tips'],
                        status='Active',
                        featured=True
                    )
                    db.session.add(job)
                    db.session.commit()
                    print(f"SYNCED_LIVE_JOB: {job.title}")
            except Exception as item_err:
                db.session.rollback()
                print(f"Notice syncing job {item.get('title')}:", item_err)
