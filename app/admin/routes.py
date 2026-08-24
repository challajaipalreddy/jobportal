from datetime import datetime, timedelta
import csv
import io
import os
import re
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Job, Company, Category, DailyJobUpdate, CareerTip, Subscriber, ContactMessage, SiteSetting, StudyMaterial
from app.forms import JobForm, CompanyForm, CategoryForm, YouTubeLinkForm
from app.utils import generate_unique_slug, extract_youtube_id

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def check_admin_access():
    if not current_user.is_admin:
        flash('Access restricted to site administrators.', 'danger')
        return redirect(url_for('main.home'))

# Helper function to get or create company
def resolve_company(company_id_val, new_company_name_val, company_logo_val=None):
    if new_company_name_val and new_company_name_val.strip():
        name_clean = new_company_name_val.strip()
        comp = Company.query.filter(Company.name.ilike(name_clean)).first()
        if not comp:
            slug = generate_unique_slug(Company, name_clean)
            comp = Company(name=name_clean, slug=slug, logo=company_logo_val)
            db.session.add(comp)
            db.session.commit()
        elif company_logo_val and not comp.logo:
            comp.logo = company_logo_val
            db.session.commit()
        return comp.id
    elif company_id_val and company_id_val > 0:
        return company_id_val
    return None

# --- STUDY MATERIALS / PDF MANAGEMENT IN ADMIN ---

@admin_bp.route('/study-materials', methods=['GET', 'POST'])
def study_materials():
    if request.method == 'POST' and 'pdf_file' in request.files:
        file = request.files['pdf_file']
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip() or 'General Placement Notes'
        description = request.form.get('description', '').strip()
        is_premium = True if request.form.get('is_premium') == '1' else False
        price = float(request.form.get('price', 99.0))
        icon = request.form.get('icon', '').strip() or 'bi-file-earmark-pdf'

        if file and file.filename.lower().endswith('.pdf') and title:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, '..', 'static', 'uploads', 'pdfs')
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, filename)
            file.save(save_path)

            slug = generate_unique_slug(StudyMaterial, title)
            material = StudyMaterial(
                title=title,
                slug=slug,
                category=category,
                description=description,
                file_path=f"static/uploads/pdfs/{filename}",
                icon=icon,
                is_premium=is_premium,
                price=price
            )
            db.session.add(material)
            db.session.commit()
            flash(f"PDF Study Material '{title}' uploaded & published!", 'success')
            return redirect(url_for('admin.study_materials'))
        else:
            flash("Failed to upload PDF. Ensure title is provided and file is a .pdf document.", 'danger')

    materials = StudyMaterial.query.order_by(StudyMaterial.created_at.desc()).all()
    price_setting = SiteSetting.query.filter_by(key='study_pass_price').first()

    return render_template('admin/study_materials.html', 
                           materials=materials, 
                           pass_price=price_setting.value if price_setting else '99',
                           title='PDF Notes Management - Admin')

@admin_bp.route('/study-materials/<int:id>/toggle-premium', methods=['POST'])
def study_material_toggle_premium(id):
    mat = StudyMaterial.query.get_or_404(id)
    mat.is_premium = not mat.is_premium
    db.session.commit()
    flash(f"Updated access mode for '{mat.title}' to {'Premium Paid' if mat.is_premium else 'Free Download'}.", 'success')
    return redirect(url_for('admin.study_materials'))

@admin_bp.route('/study-materials/<int:id>/delete', methods=['POST'])
def study_material_delete(id):
    mat = StudyMaterial.query.get_or_404(id)
    db.session.delete(mat)
    db.session.commit()
    flash('PDF Study Material deleted.', 'info')
    return redirect(url_for('admin.study_materials'))

@admin_bp.route('/settings/update-pass-price', methods=['POST'])
def update_pass_price():
    price_val = request.form.get('study_pass_price', '99').strip()
    setting = SiteSetting.query.filter_by(key='study_pass_price').first()
    if not setting:
        setting = SiteSetting(key='study_pass_price', value=price_val)
        db.session.add(setting)
    else:
        setting.value = price_val
    db.session.commit()
    flash(f'Study Pass Price updated to ₹{price_val}!', 'success')
    return redirect(url_for('admin.study_materials'))

# --- AI RAW JOB PARSER ENDPOINT ---

@admin_bp.route('/jobs/ai-parse', methods=['POST'])
def ai_parse_job():
    data = request.get_json() or {}
    raw_text = data.get('raw_text', '').strip()
    
    if not raw_text:
        return jsonify({'error': 'No raw text provided'}), 400

    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

    # 1. Company Extraction & Normalization
    company = ""
    comp_match = re.search(r'(?:Company|Organization|Hiring Company|Employer)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if comp_match:
        company = comp_match.group(1).strip()
    else:
        for l in lines[:5]:
            if any(known in l.lower() for known in ['tcs', 'tata consultancy', 'infosys', 'accenture', 'wipro', 'deloitte', 'google', 'amazon', 'microsoft', 'capgemini', 'cognizant', 'hcl']):
                company = l
                break

    # Normalize common companies
    if company:
        c_lower = company.lower()
        if 'tcs' in c_lower or 'tata consultancy' in c_lower:
            company = 'TCS (Tata Consultancy Services)'
        elif 'infosys' in c_lower:
            company = 'Infosys'
        elif 'accenture' in c_lower:
            company = 'Accenture'
        elif 'wipro' in c_lower:
            company = 'Wipro'
        elif 'deloitte' in c_lower:
            company = 'Deloitte'

    # 2. Job Title Extraction
    title = ""
    title_match = re.search(r'(?:Role|Position|Job Title|Designation|Post)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if title_match:
        title = title_match.group(1).strip()
    elif len(lines) > 0:
        title = lines[0]

    # Clean marketing fluff from title
    title = re.sub(r'^(?:Accenture|TCS|Infosys|Wipro|Deloitte|Google|Amazon)\s+(?:is\s+)?(?:hiring|inviting|looking for)\s+', '', title, flags=re.I).strip()

    # 3. Category Detection
    category_id = None
    category_name = "Software Development"
    text_lower = raw_text.lower()
    
    if 'intern' in text_lower or 'internship' in text_lower:
        category_name = "Internships"
    elif 'gov' in text_lower or 'public sector' in text_lower or 'recruitment notification' in text_lower:
        category_name = "Government Jobs"
    elif 'data scientist' in text_lower or 'machine learning' in text_lower or 'data science' in text_lower:
        category_name = "Data Science"
    elif 'data analyst' in text_lower or 'analytics' in text_lower or 'power bi' in text_lower or 'tableau' in text_lower:
        category_name = "Data Analytics"
    elif 'devops' in text_lower or 'ci/cd' in text_lower or 'kubernetes' in text_lower or 'docker' in text_lower:
        category_name = "DevOps"
    elif 'cloud' in text_lower or 'aws' in text_lower or 'azure' in text_lower or 'gcp' in text_lower:
        category_name = "Cloud"
    elif 'security' in text_lower or 'cyber' in text_lower or 'soc analyst' in text_lower or 'penetration' in text_lower:
        category_name = "Cyber Security"
    elif 'qa' in text_lower or 'testing' in text_lower or 'test engineer' in text_lower or 'selenium' in text_lower:
        category_name = "Testing"
    elif 'ui/ux' in text_lower or 'ui designer' in text_lower or 'figma' in text_lower or 'user experience' in text_lower:
        category_name = "UI/UX"

    cat_obj = Category.query.filter(Category.name.ilike(category_name)).first()
    if cat_obj:
        category_id = cat_obj.id

    # 4. Job Type & Work Mode
    job_type = "Full-Time"
    if 'intern' in text_lower or 'internship' in text_lower:
        job_type = "Internship"
    elif 'walk-in' in text_lower or 'walk in' in text_lower:
        job_type = "Walk-in Drive"
    elif 'part-time' in text_lower:
        job_type = "Part-Time"
    elif 'contract' in text_lower:
        job_type = "Contract"

    work_mode = "On-site"
    if 'remote' in text_lower or 'work from home' in text_lower or 'wfh' in text_lower:
        work_mode = "Remote"
    elif 'hybrid' in text_lower:
        work_mode = "Hybrid"

    # 5. Location Extraction & Normalization
    location = "Across India"
    loc_match = re.search(r'(?:Location|Job Location|Work Location|Locations)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if loc_match:
        loc_raw = loc_match.group(1).strip()
        location = loc_raw.replace('Bangalore', 'Bengaluru')
    elif work_mode == "Remote":
        location = "Remote"

    # 6. Experience Extraction
    experience = "0–2 Years"
    exp_match = re.search(r'(?:Experience|Exp Required|Experience Level|Exp)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if exp_match:
        experience = exp_match.group(1).strip()
    elif 'fresher' in text_lower or '2024' in text_lower or '2025' in text_lower or '2026' in text_lower:
        experience = "Freshers"

    # 7. Qualification Bullet Points
    qual_list = []
    for q in ['B.Tech', 'B.E', 'M.Tech', 'MCA', 'BCA', 'B.Sc', 'M.Sc', 'MBA']:
        if q.lower() in text_lower:
            qual_list.append(q)
    
    if qual_list:
        qualification = " / ".join(qual_list)
    else:
        qualification = "Bachelor's degree in Computer Science, IT, or related technical discipline"

    # 8. Key Skills
    found_skills = []
    for s in ['Python', 'Java', 'C++', 'SQL', 'Excel', 'JavaScript', 'HTML/CSS', 'Data Structures', 'AWS', 'Power BI', 'React', 'Problem Solving', 'Git', 'Docker']:
        if s.lower() in text_lower:
            found_skills.append(s)
    skills = ", ".join(found_skills) if found_skills else "Java, Python, SQL, Problem Solving"

    # 9. Salary / CTC
    salary = "Not disclosed"
    sal_match = re.search(r'(?:Salary|CTC|Stipend|Package|Pay)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if sal_match:
        salary = sal_match.group(1).strip()
    else:
        lpa_match = re.search(r'(\d+(?:\.\d+)?\s*(?:LPA|Lacs|Lakhs|k/month|per month))', raw_text, re.I)
        if lpa_match:
            salary = lpa_match.group(1).strip()

    # 10. Eligibility Criteria Bullet Points
    eligibility_bullets = [
        f"• {qualification} from a recognized university",
        "• Graduates from 2024–2026 batches",
        "• Minimum 60% aggregate or 6.0 CGPA throughout academics",
        "• No active backlogs at the time of joining",
        f"• Strong programming and analytical skills in {skills}"
    ]
    eligibility = "\n".join(eligibility_bullets)

    # 11. Full Job Description & Responsibilities
    description_bullets = [
        f"• Work on software development and technical engineering projects at {company or 'the hiring company'}.",
        f"• Design, develop, test, and maintain scalable applications for the {title or 'Software Engineering'} role.",
        "• Collaborate with engineering team leads, technical architects, and product managers.",
        "• Troubleshoot bugs, optimize query performance, and write efficient, clean code.",
        "• Follow software engineering best practices, code reviews, and testing protocols."
    ]
    description = "\n".join(description_bullets)

    responsibilities_bullets = [
        f"• Develop and maintain software components according to client and product requirements.",
        "• Write clean, scalable, and well-documented code in primary technologies.",
        "• Debug and resolve technical production issues in a timely manner.",
        "• Participate in team agile sprints, technical code reviews, and quality assurance."
    ]
    responsibilities = "\n".join(responsibilities_bullets)

    # 12. Application URL & Deadline
    app_url = ""
    url_match = re.search(r'https?://[^\s]+', raw_text)
    if url_match:
        app_url = url_match.group(0)

    deadline = ""
    dl_match = re.search(r'(?:Deadline|Last Date|Apply Before)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if dl_match:
        deadline = dl_match.group(1).strip()

    # 13. Campus to Career Guidance Generation
    c_name = company or "The hiring organization"
    t_name = title or "Software Engineer"
    
    campus_analysis = f"• Strong entry-level career opportunity at {c_name} for the {t_name} role.\n• Provides hands-on exposure to modern software frameworks, enterprise tools, and real-world project lifecycles.\n• Excellent learning environment for freshers building a foundational engineering career."
    who_can_apply = f"Suitable for final-year students, recent passouts ({qualification}), and early-career candidates with strong fundamentals in {skills}."
    resume_tips = f"• Highlight academic and personal projects involving {skills} on page 1 of your resume.\n• Include clickable links to verified GitHub repositories or live web demos.\n• Quantify project results and clearly list your specific technical contribution."
    interview_tips = f"• Revise core programming fundamentals and Data Structures (Arrays, Strings, HashMaps).\n• Practice SQL queries (JOINs, GROUP BY, Aggregate functions).\n• Be ready to explain your resume projects in detail including design decisions and challenges faced."

    return jsonify({
        'company': company,
        'category_id': category_id,
        'category_name': category_name,
        'title': title,
        'qualification': qualification,
        'experience': experience,
        'salary': salary,
        'location': location,
        'work_mode': work_mode,
        'job_type': job_type,
        'skills': skills,
        'application_url': app_url,
        'application_deadline': deadline,
        'description': description,
        'responsibilities': responsibilities,
        'eligibility': eligibility,
        'campus_analysis': campus_analysis,
        'who_can_apply': who_can_apply,
        'resume_tips': resume_tips,
        'interview_tips': interview_tips
    })


# --- AUTO GENERATE CAMPUS ANALYSIS API ---

@admin_bp.route('/jobs/generate-analysis', methods=['POST'])
def generate_analysis():
    data = request.get_json() or {}
    company_name = data.get('company', '').strip() or 'The hiring company'
    title = data.get('title', '').strip() or 'Job Position'
    qualification = data.get('qualification', '').strip() or 'Engineering / Science / Computer Graduates'
    experience = data.get('experience', '').strip() or '0–2 Years (Freshers)'
    skills = data.get('skills', '').strip() or 'Core technical & analytical skills'
    eligibility = data.get('eligibility', '').strip() or 'Recent passouts and final-year students'

    campus_analysis = f"High-priority hiring drive at {company_name} for the {title} role. Ideal for fresh graduates and early-career job seekers looking for strong career growth, structured training, and excellent corporate exposure."
    who_can_apply = f"Candidates pursuing or completed {qualification} with experience level ({experience}). Must have foundational knowledge in {skills}."
    resume_tips = f"1. Keep resume to a single page and highlight relevant academic/personal projects related to {skills}.\n2. Feature verified GitHub repository links or project portfolio on the top header.\n3. Quantify achievements (e.g. 'Developed full-stack web application used by 200+ users')."
    interview_tips = f"Round 1: Online Aptitude & Logical Assessment (Quantitative Aptitude, Verbal & Pseudo-code).\nRound 2: Technical Assessment & Live Coding (Focus on {skills} & Problem Solving).\nRound 3: HR & Management Discussion (Communication skills & role alignment)."

    return jsonify({
        'campus_analysis': campus_analysis,
        'who_can_apply': who_can_apply,
        'resume_tips': resume_tips,
        'interview_tips': interview_tips
    })

# --- TODAY'S CONTROL CENTER ---

@admin_bp.route('/today')
def today_control():
    today_date = datetime.utcnow().date()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    published_today = Job.query.filter(Job.posted_date >= today_start, Job.status == 'Active').all()
    drafts_today = Job.query.filter(Job.posted_date >= today_start, Job.status == 'Draft').all()
    expiring_soon = Job.query.filter(
        Job.status == 'Active',
        Job.application_deadline.isnot(None),
        Job.application_deadline >= today_date,
        Job.application_deadline <= (today_date + timedelta(days=2))
    ).all()
    
    daily_updates = DailyJobUpdate.query.order_by(DailyJobUpdate.update_date.desc()).limit(5).all()

    return render_template('admin/today.html',
                           today_date=today_date,
                           published_today=published_today,
                           drafts_today=drafts_today,
                           expiring_soon=expiring_soon,
                           daily_updates=daily_updates,
                           title="Today's Job Control Center - Admin")

@admin_bp.route('/dashboard')
def dashboard():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_date = datetime.utcnow().date()
    three_days_from_now = today_date + timedelta(days=3)
    
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(status='Active').count()
    expired_jobs = Job.query.filter(
        (Job.status == 'Expired') | 
        ((Job.application_deadline.isnot(None)) & (Job.application_deadline < today_date))
    ).count()
    draft_jobs = Job.query.filter_by(status='Draft').count()
    
    total_companies = Company.query.count()
    total_views = db.session.query(db.func.sum(Job.views)).scalar() or 0
    jobs_today = Job.query.filter(Job.posted_date >= today_start).count()
    
    expiring_soon_jobs = Job.query.filter(
        Job.status == 'Active',
        Job.application_deadline.isnot(None),
        Job.application_deadline >= today_date,
        Job.application_deadline <= three_days_from_now
    ).order_by(Job.application_deadline.asc()).all()
    
    youtube_jobs_count = Job.query.filter(
        Job.youtube_video_id.isnot(None), 
        Job.youtube_video_id != ''
    ).count()
    
    recent_jobs = Job.query.order_by(Job.posted_date.desc()).limit(5).all()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    total_subscribers = Subscriber.query.filter_by(is_active=True).count()

    return render_template('admin/dashboard.html',
                           total_jobs=total_jobs,
                           active_jobs=active_jobs,
                           expired_jobs=expired_jobs,
                           draft_jobs=draft_jobs,
                           total_companies=total_companies,
                           total_views=total_views,
                           jobs_today=jobs_today,
                           expiring_soon_jobs=expiring_soon_jobs,
                           youtube_jobs_count=youtube_jobs_count,
                           recent_jobs=recent_jobs,
                           recent_messages=recent_messages,
                           total_subscribers=total_subscribers,
                           title="Admin Dashboard - Campus to Career")

# --- JOBS MANAGEMENT ---

@admin_bp.route('/jobs')
def jobs_list():
    page = request.args.get('page', 1, type=int)
    search_q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    query = Job.query
    if search_q:
        query = query.filter(Job.title.ilike(f"%{search_q}%"))
    if status_filter:
        query = query.filter(Job.status == status_filter)
        
    query = query.order_by(Job.posted_date.desc())
    paginated = query.paginate(page=page, per_page=15, error_out=False)

    return render_template('admin/jobs_list.html',
                           jobs=paginated.items,
                           pagination=paginated,
                           search_q=search_q,
                           status_filter=status_filter,
                           title="Manage Jobs - Admin Panel")

@admin_bp.route('/jobs/new', methods=['GET', 'POST'])
def job_create():
    form = JobForm()
    
    companies = Company.query.order_by(Company.name.asc()).all()
    form.company_id.choices = [(0, '-- Select Existing Company OR Type Below --')] + [(c.id, c.name) for c in companies]
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(0, '-- Select Category --')] + [(cat.id, cat.name) for cat in categories]

    possible_duplicate = None

    if request.method == 'POST':
        comp_id = resolve_company(form.company_id.data, form.new_company_name.data, form.company_logo.data)
        title_val = form.title.data.strip() if form.title.data else ''
        
        if comp_id and title_val:
            existing_duplicate = Job.query.filter(
                Job.company_id == comp_id,
                Job.title.ilike(f"%{title_val}%")
            ).first()

            if existing_duplicate and not request.form.get('force_publish'):
                possible_duplicate = existing_duplicate

    if form.validate_on_submit() and not possible_duplicate:
        final_company_id = resolve_company(form.company_id.data, form.new_company_name.data, form.company_logo.data)
        
        if not final_company_id:
            flash('Please select an existing company or type a new company name.', 'danger')
            return render_template('admin/job_form.html', form=form, action='Create', title='Add New Job - Admin')
            
        slug = generate_unique_slug(Job, form.title.data)
        yt_id = extract_youtube_id(form.youtube_video_url.data)
        category_id_val = form.category_id.data if form.category_id.data != 0 else None
        
        job = Job(
            title=form.title.data.strip(),
            slug=slug,
            company_id=final_company_id,
            company_logo=form.company_logo.data.strip() if form.company_logo.data else None,
            category_id=category_id_val,
            job_type=form.job_type.data,
            location=form.location.data.strip() if form.location.data else 'India',
            work_mode=form.work_mode.data,
            qualification=form.qualification.data.strip() if form.qualification.data else None,
            experience=form.experience.data.strip() if form.experience.data else '0–2 Years',
            skills=form.skills.data.strip() if form.skills.data else None,
            eligibility=form.eligibility.data.strip() if form.eligibility.data else None,
            short_description=form.description.data.strip()[:250] if form.description.data else None,
            description=form.description.data.strip(),
            responsibilities=form.responsibilities.data.strip() if form.responsibilities.data else None,
            salary=form.salary.data.strip() if form.salary.data else None,
            application_url=form.application_url.data.strip(),
            source_url=form.source_url.data.strip() if form.source_url.data else None,
            application_deadline=form.application_deadline.data,
            campus_analysis=form.campus_analysis.data.strip() if form.campus_analysis.data else None,
            who_can_apply=form.who_can_apply.data.strip() if form.who_can_apply.data else None,
            resume_tips=form.resume_tips.data.strip() if form.resume_tips.data else None,
            interview_tips=form.interview_tips.data.strip() if form.interview_tips.data else None,
            admin_notes=form.admin_notes.data.strip() if form.admin_notes.data else None,
            youtube_video_url=form.youtube_video_url.data.strip() if form.youtube_video_url.data else None,
            youtube_video_id=yt_id,
            youtube_title=form.youtube_title.data.strip() if form.youtube_title.data else None,
            youtube_thumbnail=f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else None,
            seo_title=form.seo_title.data.strip() if form.seo_title.data else None,
            seo_description=form.seo_description.data.strip() if form.seo_description.data else None,
            seo_keywords=form.seo_keywords.data.strip() if form.seo_keywords.data else None,
            status=form.status.data,
            featured=form.featured.data
        )
        db.session.add(job)
        db.session.commit()
        flash('Job published successfully!', 'success')
        return redirect(url_for('admin.jobs_list'))

    return render_template('admin/job_form.html', form=form, possible_duplicate=possible_duplicate, action='Create', title='Add New Job - Admin')

@admin_bp.route('/jobs/<int:id>/edit', methods=['GET', 'POST'])
def job_edit(id):
    job = Job.query.get_or_404(id)
    form = JobForm(obj=job)
    
    companies = Company.query.order_by(Company.name.asc()).all()
    form.company_id.choices = [(0, '-- Select Existing Company OR Type Below --')] + [(c.id, c.name) for c in companies]
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(0, '-- Select Category --')] + [(cat.id, cat.name) for cat in categories]

    if request.method == 'GET':
        form.category_id.data = job.category_id if job.category_id else 0
        form.company_id.data = job.company_id

    if form.validate_on_submit():
        final_company_id = resolve_company(form.company_id.data, form.new_company_name.data, form.company_logo.data) or job.company_id
        
        if job.title != form.title.data.strip():
            job.slug = generate_unique_slug(Job, form.title.data, current_id=job.id)
            
        job.title = form.title.data.strip()
        job.company_id = final_company_id
        job.company_logo = form.company_logo.data.strip() if form.company_logo.data else None
        job.category_id = form.category_id.data if form.category_id.data != 0 else None
        job.job_type = form.job_type.data
        job.location = form.location.data.strip() if form.location.data else 'India'
        job.work_mode = form.work_mode.data
        job.qualification = form.qualification.data.strip() if form.qualification.data else None
        job.experience = form.experience.data.strip() if form.experience.data else '0–2 Years'
        job.skills = form.skills.data.strip() if form.skills.data else None
        job.eligibility = form.eligibility.data.strip() if form.eligibility.data else None
        job.short_description = form.description.data.strip()[:250] if form.description.data else None
        job.description = form.description.data.strip()
        job.responsibilities = form.responsibilities.data.strip() if form.responsibilities.data else None
        job.salary = form.salary.data.strip() if form.salary.data else None
        job.application_url = form.application_url.data.strip()
        job.source_url = form.source_url.data.strip() if form.source_url.data else None
        job.application_deadline = form.application_deadline.data
        job.campus_analysis = form.campus_analysis.data.strip() if form.campus_analysis.data else None
        job.who_can_apply = form.who_can_apply.data.strip() if form.who_can_apply.data else None
        job.resume_tips = form.resume_tips.data.strip() if form.resume_tips.data else None
        job.interview_tips = form.interview_tips.data.strip() if form.interview_tips.data else None
        job.admin_notes = form.admin_notes.data.strip() if form.admin_notes.data else None
        
        yt_id = extract_youtube_id(form.youtube_video_url.data)
        job.youtube_video_url = form.youtube_video_url.data.strip() if form.youtube_video_url.data else None
        job.youtube_video_id = yt_id
        job.youtube_title = form.youtube_title.data.strip() if form.youtube_title.data else None
        job.youtube_thumbnail = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else None
        
        job.seo_title = form.seo_title.data.strip() if form.seo_title.data else None
        job.seo_description = form.seo_description.data.strip() if form.seo_description.data else None
        job.seo_keywords = form.seo_keywords.data.strip() if form.seo_keywords.data else None
        job.status = form.status.data
        job.featured = form.featured.data

        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('admin.jobs_list'))

    return render_template('admin/job_form.html', form=form, job=job, action='Edit', title=f"Edit Job - {job.title}")

@admin_bp.route('/jobs/<int:id>/quick-video', methods=['POST'])
def job_quick_video(id):
    job = Job.query.get_or_404(id)
    yt_url = request.form.get('youtube_video_url', '').strip()
    if yt_url:
        yt_id = extract_youtube_id(yt_url)
        job.youtube_video_url = yt_url
        job.youtube_video_id = yt_id
        job.youtube_title = request.form.get('youtube_title', '').strip() or job.title
        job.youtube_thumbnail = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else None
        db.session.commit()
        flash(f"YouTube video linked to '{job.title}'!", 'success')
    return redirect(url_for('admin.jobs_list'))

@admin_bp.route('/jobs/<int:id>/duplicate', methods=['POST'])
def job_duplicate(id):
    original = Job.query.get_or_404(id)
    new_title = f"{original.title} (Copy)"
    new_slug = generate_unique_slug(Job, new_title)
    
    copy_job = Job(
        title=new_title,
        slug=new_slug,
        company_id=original.company_id,
        company_logo=original.company_logo,
        category_id=original.category_id,
        job_type=original.job_type,
        location=original.location,
        work_mode=original.work_mode,
        qualification=original.qualification,
        experience=original.experience,
        skills=original.skills,
        eligibility=original.eligibility,
        short_description=original.short_description,
        description=original.description,
        responsibilities=original.responsibilities,
        salary=original.salary,
        application_url=original.application_url,
        source_url=original.source_url,
        application_deadline=original.application_deadline,
        campus_analysis=original.campus_analysis,
        who_can_apply=original.who_can_apply,
        resume_tips=original.resume_tips,
        interview_tips=original.interview_tips,
        admin_notes=original.admin_notes,
        youtube_video_url=original.youtube_video_url,
        youtube_video_id=original.youtube_video_id,
        youtube_title=original.youtube_title,
        youtube_thumbnail=original.youtube_thumbnail,
        status='Draft',
        featured=False
    )
    db.session.add(copy_job)
    db.session.commit()
    flash('Job duplicated as Draft.', 'success')
    return redirect(url_for('admin.job_edit', id=copy_job.id))

@admin_bp.route('/jobs/<int:id>/delete', methods=['POST'])
def job_delete(id):
    job = Job.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted permanently.', 'info')
    return redirect(url_for('admin.jobs_list'))

@admin_bp.route('/jobs/<int:id>/toggle-featured', methods=['POST'])
def job_toggle_featured(id):
    job = Job.query.get_or_404(id)
    job.featured = not job.featured
    db.session.commit()
    flash(f"Featured status updated for '{job.title}'.", 'success')
    return redirect(url_for('admin.jobs_list'))

@admin_bp.route('/jobs/bulk-action', methods=['POST'])
def jobs_bulk_action():
    action = request.form.get('bulk_action')
    job_ids = request.form.getlist('selected_jobs')
    
    if not job_ids:
        flash('No jobs selected for bulk action.', 'warning')
        return redirect(url_for('admin.jobs_list'))
        
    jobs = Job.query.filter(Job.id.in_([int(i) for i in job_ids])).all()
    count = len(jobs)
    
    if action == 'publish':
        for j in jobs: j.status = 'Active'
        flash(f'Published {count} selected jobs.', 'success')
    elif action == 'unpublish':
        for j in jobs: j.status = 'Draft'
        flash(f'Marked {count} jobs as Draft.', 'info')
    elif action == 'expire':
        for j in jobs: j.status = 'Expired'
        flash(f'Marked {count} jobs as Expired.', 'warning')
    elif action == 'feature':
        for j in jobs: j.featured = True
        flash(f'Marked {count} jobs as Featured.', 'success')
    elif action == 'delete':
        for j in jobs: db.session.delete(j)
        flash(f'Deleted {count} jobs.', 'danger')
        
    db.session.commit()
    return redirect(url_for('admin.jobs_list'))

# --- BULK CSV / EXCEL IMPORT ---

@admin_bp.route('/jobs/template.csv')
def download_csv_template():
    output = io.StringIO()
    writer = csv.writer(output)
    header = [
        'company', 'company_logo', 'title', 'category', 'location', 'experience', 'qualification',
        'job_type', 'work_mode', 'skills', 'salary', 'short_description',
        'description', 'responsibilities', 'eligibility', 'application_url',
        'source_url', 'posted_date', 'application_deadline', 'youtube_url', 'featured', 'status'
    ]
    writer.writerow(header)
    sample_row = [
        'TCS', 'https://upload.wikimedia.org/wikipedia/commons/b/b1/Tata_Consultancy_Services_Logo.svg',
        'Software Engineer Freshers', 'Software Development', 'India', '0–2 Years',
        'B.Tech / B.E', 'Full-Time', 'On-site', 'Java, Python, SQL', '3.36 LPA',
        'TCS Hiring Freshers across India', 'Full details description here...',
        'Develop software modules', '60% throughout academics', 'https://tcs.com/apply',
        'https://tcs.com', '2026-08-14', '2026-08-30', 'https://youtu.be/dQw4w9WgXcQ', 'Yes', 'Active'
    ]
    writer.writerow(sample_row)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=jobs_import_template.csv"}
    )

@admin_bp.route('/jobs/export')
def export_jobs_csv():
    status_filter = request.args.get('status', '').strip()
    query = Job.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    jobs = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Company', 'Title', 'Category', 'Location', 'Experience', 'Job Type', 'Status', 'Views', 'Application URL', 'Posted Date'])
    
    for j in jobs:
        writer.writerow([
            j.id, j.company.name, j.title, j.category.name if j.category else '',
            j.location, j.experience, j.job_type, j.status, j.views,
            j.application_url, j.posted_date.strftime('%Y-%m-%d')
        ])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=campus_to_career_jobs.csv"}
    )

@admin_bp.route('/jobs/import', methods=['GET', 'POST'])
def jobs_import():
    preview_rows = []
    
    if request.method == 'POST' and 'import_file' in request.files:
        file = request.files['import_file']
        filename = file.filename.lower()
        
        rows_data = []
        if filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.DictReader(stream)
            rows_data = list(csv_reader)
        elif filename.endswith('.xlsx'):
            import openpyxl
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            header = [str(cell.value or '').strip() for cell in sheet[1]]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(row):
                    rows_data.append(dict(zip(header, row)))

        for idx, row in enumerate(rows_data, start=1):
            comp_name = str(row.get('company') or '').strip()
            title = str(row.get('title') or '').strip()
            app_url = str(row.get('application_url') or '').strip()
            category_name = str(row.get('category') or '').strip()
            comp_logo = str(row.get('company_logo') or '').strip()
            
            errors = []
            if not comp_name: errors.append('Missing Company')
            if not title: errors.append('Missing Job Title')
            if not app_url or not app_url.startswith('http'): errors.append('Invalid Application URL')
            
            comp = Company.query.filter(Company.name.ilike(comp_name)).first() if comp_name else None
            cat = Category.query.filter(Category.name.ilike(category_name)).first() if category_name else None
            
            dup = None
            if comp and title:
                dup = Job.query.filter(Job.company_id == comp.id, Job.title.ilike(title)).first()

            status = 'Ready'
            if errors:
                status = 'Error'
            elif dup:
                status = 'Warning (Possible Duplicate)'

            preview_rows.append({
                'row_num': idx,
                'company_name': comp_name,
                'company_logo': comp_logo,
                'title': title,
                'category_name': category_name,
                'location': row.get('location', 'India'),
                'experience': row.get('experience', '0–2 Years'),
                'qualification': row.get('qualification', ''),
                'job_type': row.get('job_type', 'Full-Time'),
                'work_mode': row.get('work_mode', 'On-site'),
                'skills': row.get('skills', ''),
                'salary': row.get('salary', ''),
                'short_description': row.get('short_description', ''),
                'description': row.get('description', title),
                'responsibilities': row.get('responsibilities', ''),
                'eligibility': row.get('eligibility', ''),
                'application_url': app_url,
                'source_url': row.get('source_url', ''),
                'application_deadline': row.get('application_deadline', ''),
                'youtube_url': row.get('youtube_url', ''),
                'featured': True if str(row.get('featured')).lower() in ['yes', 'true', '1'] else False,
                'status_val': str(row.get('status', 'Active')).capitalize(),
                'errors': errors,
                'status': status
            })

    if request.method == 'POST' and 'confirm_import' in request.form:
        import_count = 0
        total_rows = int(request.form.get('total_rows', 0))
        
        for i in range(1, total_rows + 1):
            if request.form.get(f'include_row_{i}') == '1':
                comp_name = request.form.get(f'company_{i}', '').strip()
                comp_logo = request.form.get(f'company_logo_{i}', '').strip()
                title = request.form.get(f'title_{i}', '').strip()
                app_url = request.form.get(f'application_url_{i}', '').strip()
                cat_name = request.form.get(f'category_{i}', '').strip()
                
                if comp_name and title and app_url:
                    comp = Company.query.filter(Company.name.ilike(comp_name)).first()
                    if not comp:
                        comp = Company(name=comp_name, slug=generate_unique_slug(Company, comp_name), logo=comp_logo or None)
                        db.session.add(comp)
                        db.session.commit()
                    elif comp_logo and not comp.logo:
                        comp.logo = comp_logo
                        db.session.commit()
                        
                    cat = Category.query.filter(Category.name.ilike(cat_name)).first() if cat_name else None
                    
                    slug = generate_unique_slug(Job, title)
                    yt_url = request.form.get(f'youtube_url_{i}', '').strip()
                    yt_id = extract_youtube_id(yt_url)
                    
                    deadline_val = None
                    d_str = request.form.get(f'application_deadline_{i}', '').strip()
                    if d_str:
                        try: deadline_val = datetime.strptime(d_str, '%Y-%m-%d').date()
                        except: pass
                    
                    job = Job(
                        title=title,
                        slug=slug,
                        company_id=comp.id,
                        company_logo=comp_logo or None,
                        category_id=cat.id if cat else None,
                        location=request.form.get(f'location_{i}', 'India'),
                        experience=request.form.get(f'experience_{i}', '0–2 Years'),
                        qualification=request.form.get(f'qualification_{i}', ''),
                        job_type=request.form.get(f'job_type_{i}', 'Full-Time'),
                        work_mode=request.form.get(f'work_mode_{i}', 'On-site'),
                        skills=request.form.get(f'skills_{i}', ''),
                        salary=request.form.get(f'salary_{i}', ''),
                        short_description=request.form.get(f'short_description', ''),
                        description=request.form.get(f'description_{i}', title),
                        responsibilities=request.form.get(f'responsibilities_{i}', ''),
                        eligibility=request.form.get(f'eligibility_{i}', ''),
                        application_url=app_url,
                        source_url=request.form.get(f'source_url_{i}', ''),
                        application_deadline=deadline_val,
                        youtube_video_url=yt_url or None,
                        youtube_video_id=yt_id,
                        youtube_thumbnail=f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else None,
                        featured=True if request.form.get(f'featured_{i}') == '1' else False,
                        status=request.form.get(f'status_val_{i}', 'Active')
                    )
                    db.session.add(job)
                    import_count += 1
                    
        db.session.commit()
        flash(f'Successfully imported {import_count} jobs!', 'success')
        return redirect(url_for('admin.jobs_list'))

    return render_template('admin/jobs_import.html', preview_rows=preview_rows, title='Bulk Import Jobs - Admin')

# --- DAILY YOUTUBE VIDEO UPDATE ---

@admin_bp.route('/daily-video', methods=['GET', 'POST'])
def daily_video():
    if request.method == 'POST':
        date_str = request.form.get('update_date')
        title = request.form.get('title')
        yt_url = request.form.get('youtube_video_url')
        job_ids = request.form.getlist('selected_jobs')
        
        if title and date_str and job_ids:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                dt = datetime.utcnow().date()
                
            slug = generate_unique_slug(DailyJobUpdate, title)
            yt_id = extract_youtube_id(yt_url)
            
            jobs = Job.query.filter(Job.id.in_([int(i) for i in job_ids])).all()
            
            desc_lines = [f"TODAY'S TOP JOBS ({dt.strftime('%d %B %Y').upper()}):", ""]
            for idx, j in enumerate(jobs, start=1):
                desc_lines.append(f"{idx}. {j.company.name} - {j.title}")
                desc_lines.append(f"{request.host_url.rstrip('/')}/jobs/{j.slug}")
                desc_lines.append("")
            desc_lines.append("Subscribe to Campus to Career for daily hiring updates!")
            
            generated_desc = "\n".join(desc_lines)
            
            daily_up = DailyJobUpdate(
                title=title,
                slug=slug,
                update_date=dt,
                youtube_video_url=yt_url,
                youtube_video_id=yt_id,
                youtube_description=generated_desc
            )
            db.session.add(daily_up)
            db.session.commit()
            
            for j in jobs:
                j.daily_update_id = daily_up.id
                if yt_id and not j.youtube_video_id:
                    j.youtube_video_url = yt_url
                    j.youtube_video_id = yt_id
                    j.youtube_thumbnail = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
            db.session.commit()
            
            flash('Daily Job Video Update created successfully!', 'success')
            return redirect(url_for('admin.daily_video'))

    recent_updates = DailyJobUpdate.query.order_by(DailyJobUpdate.update_date.desc()).all()
    active_jobs = Job.query.filter_by(status='Active').order_by(Job.posted_date.desc()).limit(20).all()

    return render_template('admin/daily_video.html', 
                           recent_updates=recent_updates, 
                           active_jobs=active_jobs, 
                           today_date=datetime.utcnow().date().strftime('%Y-%m-%d'),
                           title='Daily Job Video Updates - Admin')

# --- COMPANY MANAGEMENT ---

@admin_bp.route('/companies')
def companies_list():
    companies = Company.query.order_by(Company.name.asc()).all()
    form = CompanyForm()
    return render_template('admin/companies_list.html', companies=companies, form=form, title='Manage Companies - Admin')

@admin_bp.route('/companies/new', methods=['POST'])
def company_create():
    form = CompanyForm()
    if form.validate_on_submit():
        slug = generate_unique_slug(Company, form.name.data)
        comp = Company(
            name=form.name.data.strip(),
            slug=slug,
            logo=form.logo.data.strip() if form.logo.data else None,
            website=form.website.data.strip() if form.website.data else None,
            description=form.description.data.strip() if form.description.data else None
        )
        db.session.add(comp)
        db.session.commit()
        flash('Company added successfully!', 'success')
    else:
        flash('Failed to add company. Check inputs.', 'danger')
    return redirect(url_for('admin.companies_list'))

@admin_bp.route('/companies/<int:id>/delete', methods=['POST'])
def company_delete(id):
    comp = Company.query.get_or_404(id)
    db.session.delete(comp)
    db.session.commit()
    flash('Company deleted.', 'info')
    return redirect(url_for('admin.companies_list'))

# --- CATEGORY MANAGEMENT ---

@admin_bp.route('/categories')
def categories_list():
    categories = Category.query.order_by(Category.name.asc()).all()
    form = CategoryForm()
    return render_template('admin/categories_list.html', categories=categories, form=form, title='Manage Categories - Admin')

@admin_bp.route('/categories/new', methods=['POST'])
def category_create():
    form = CategoryForm()
    if form.validate_on_submit():
        slug = generate_unique_slug(Category, form.name.data)
        cat = Category(
            name=form.name.data.strip(),
            slug=slug,
            description=form.description.data.strip() if form.description.data else None,
            icon=form.icon.data.strip() if form.icon.data else 'bi-briefcase'
        )
        db.session.add(cat)
        db.session.commit()
        flash('Category added successfully!', 'success')
    else:
        flash('Failed to add category.', 'danger')
    return redirect(url_for('admin.categories_list'))

@admin_bp.route('/categories/<int:id>/delete', methods=['POST'])
def category_delete(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'info')
    return redirect(url_for('admin.categories_list'))

# --- YOUTUBE INTEGRATION ---

@admin_bp.route('/youtube', methods=['GET', 'POST'])
def youtube_list():
    form = YouTubeLinkForm()
    jobs = Job.query.order_by(Job.posted_date.desc()).all()
    form.job_id.choices = [(j.id, f"{j.company.name} - {j.title}") for j in jobs]
    
    if form.validate_on_submit():
        job = Job.query.get(form.job_id.data)
        if job:
            yt_id = extract_youtube_id(form.youtube_video_url.data)
            job.youtube_video_url = form.youtube_video_url.data.strip()
            job.youtube_video_id = yt_id
            job.youtube_title = form.youtube_title.data.strip() if form.youtube_title.data else job.title
            job.youtube_thumbnail = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else None
            db.session.commit()
            flash(f"YouTube video linked to job '{job.title}'!", 'success')
            return redirect(url_for('admin.youtube_list'))

    youtube_jobs = Job.query.filter(
        Job.youtube_video_id.isnot(None), 
        Job.youtube_video_id != ''
    ).order_by(Job.posted_date.desc()).all()
    
    return render_template('admin/youtube_list.html', 
                           youtube_jobs=youtube_jobs, 
                           form=form, 
                           title='YouTube Video Integrations - Admin')

# --- SUBSCRIBERS MANAGEMENT ---

@admin_bp.route('/subscribers')
def subscribers_list():
    subscribers = Subscriber.query.order_by(Subscriber.subscribed_at.desc()).all()
    return render_template('admin/subscribers_list.html', subscribers=subscribers, title='Newsletter Subscribers - Admin')

@admin_bp.route('/subscribers/export')
def subscribers_export():
    subscribers = Subscriber.query.filter_by(is_active=True).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Email', 'Subscribed Date'])
    for sub in subscribers:
        writer.writerow([sub.id, sub.email, sub.subscribed_at.strftime('%Y-%m-%d %H:%M:%S')])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=campus_to_career_subscribers.csv"}
    )

# --- CONTACT MESSAGES ---

@admin_bp.route('/messages')
def messages_list():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages_list.html', messages=messages, title='Contact Messages - Admin')

@admin_bp.route('/messages/<int:id>/read', methods=['POST'])
def message_mark_read(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin.messages_list'))

# --- SITE SETTINGS ---

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        announcement = request.form.get('announcement_banner', '').strip()
        setting = SiteSetting.query.filter_by(key='announcement_banner').first()
        if not setting:
            setting = SiteSetting(key='announcement_banner', value=announcement)
            db.session.add(setting)
        else:
            setting.value = announcement

        pass_price = request.form.get('study_pass_price', '99').strip()
        price_setting = SiteSetting.query.filter_by(key='study_pass_price').first()
        if not price_setting:
            price_setting = SiteSetting(key='study_pass_price', value=pass_price)
            db.session.add(price_setting)
        else:
            price_setting.value = pass_price

        upi_id = request.form.get('upi_id', 'campustocareer@upi').strip()
        upi_setting = SiteSetting.query.filter_by(key='upi_id').first()
        if not upi_setting:
            upi_setting = SiteSetting(key='upi_id', value=upi_id)
            db.session.add(upi_setting)
        else:
            upi_setting.value = upi_id

        db.session.commit()
        flash('Website settings saved!', 'success')
        return redirect(url_for('admin.settings'))

    announcement_setting = SiteSetting.query.filter_by(key='announcement_banner').first()
    price_setting = SiteSetting.query.filter_by(key='study_pass_price').first()
    upi_setting = SiteSetting.query.filter_by(key='upi_id').first()

    return render_template('admin/settings.html', 
                           announcement=announcement_setting.value if announcement_setting else '',
                           pass_price=price_setting.value if price_setting else '99',
                           upi_id=upi_setting.value if upi_setting else 'campustocareer@upi',
                           title='Website Settings - Admin')

# --- PAYMENT SUBMISSIONS ---

@admin_bp.route('/payments')
def payments_list():
    payments = PaymentSubmission.query.order_by(PaymentSubmission.created_at.desc()).all()
    return render_template('admin/payments_list.html', payments=payments, title='UPI Payment Submissions - Admin')

@admin_bp.route('/payments/<int:id>/delete', methods=['POST'])
def payment_delete(id):
    pay = PaymentSubmission.query.get_or_404(id)
    db.session.delete(pay)
    db.session.commit()
    flash('Payment submission deleted.', 'info')
    return redirect(url_for('admin.payments_list'))

# --- AI AUTOPILOT JOB CRAWLER ---

from app.admin.ai_autopilot import run_ai_autopilot_crawler

@admin_bp.route('/ai-autopilot', methods=['GET', 'POST'])
def ai_autopilot():
    setting = SiteSetting.query.filter_by(key='autopilot_auto_publish').first()
    auto_publish = (setting.value == 'true') if setting else True

    last_run = SiteSetting.query.filter_by(key='autopilot_last_run').first()

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'toggle_setting':
            pub_mode = request.form.get('auto_publish')
            if not setting:
                setting = SiteSetting(key='autopilot_auto_publish', value=pub_mode)
                db.session.add(setting)
            else:
                setting.value = pub_mode
            db.session.commit()
            flash(f"AI Autopilot mode updated to {'Auto-Publish Live' if pub_mode == 'true' else 'Save as Drafts'}.", 'success')
            return redirect(url_for('admin.ai_autopilot'))

        if action == 'run_crawler':
            result = run_ai_autopilot_crawler(auto_publish=auto_publish)
            
            lr_setting = SiteSetting.query.filter_by(key='autopilot_last_run').first()
            now_str = datetime.utcnow().strftime('%d %B %Y, %I:%M %p UTC')
            if not lr_setting:
                lr_setting = SiteSetting(key='autopilot_last_run', value=now_str)
                db.session.add(lr_setting)
            else:
                lr_setting.value = now_str
            db.session.commit()

            flash(f"🤖 AI Autopilot successfully fetched and created {result['created_count']} jobs from official company career portals!", 'success')
            return render_template('admin/ai_autopilot.html', 
                                   auto_publish=auto_publish,
                                   last_run=now_str,
                                   logs=result['logs'],
                                   title='AI Autopilot Job Finder - Admin')

    return render_template('admin/ai_autopilot.html', 
                           auto_publish=auto_publish,
                           last_run=last_run.value if last_run else 'Never',
                           logs=None,
                           title='AI Autopilot Job Finder - Admin')


