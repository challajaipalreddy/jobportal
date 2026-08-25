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

from app.main.routes import PRESET_STUDY_MATERIALS, get_deleted_preset_ids

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

    deleted_ids = get_deleted_preset_ids()
    materials_list = []

    # Include non-deleted preset PDFs
    for cat_name, notes in PRESET_STUDY_MATERIALS.items():
        for note in notes:
            if note['id'] not in deleted_ids:
                materials_list.append({
                    'id': note['id'],
                    'title': note['title'],
                    'category': cat_name,
                    'file_path': note['file'],
                    'download_count': 'Preset',
                    'is_preset': True,
                    'created_at': 'System Note'
                })

    # Include custom uploaded DB materials
    try:
        db_mats = StudyMaterial.query.order_by(StudyMaterial.created_at.desc()).all()
        for m in db_mats:
            materials_list.insert(0, {
                'id': f'db-{m.id}',
                'title': m.title,
                'category': m.category,
                'file_path': f'db:{m.id}',
                'download_count': m.download_count,
                'is_preset': False,
                'created_at': m.created_at.strftime('%b %d, %Y')
            })
    except Exception:
        pass

    price_setting = SiteSetting.query.filter_by(key='study_pass_price').first()

    return render_template('admin/study_materials.html', 
                           materials=materials_list, 
                           pass_price=price_setting.value if price_setting else '99',
                           title='PDF Notes Management - Admin')

@admin_bp.route('/study-materials/<path:id>/delete', methods=['POST'])
def study_material_delete(id):
    if str(id).startswith('preset-'):
        deleted_ids = get_deleted_preset_ids()
        deleted_ids.add(str(id))
        setting = SiteSetting.query.filter_by(key='deleted_preset_notes').first()
        if not setting:
            setting = SiteSetting(key='deleted_preset_notes', value=",".join(deleted_ids))
            db.session.add(setting)
        else:
            setting.value = ",".join(deleted_ids)
        db.session.commit()
        flash('Preset PDF note deleted from library.', 'info')
    else:
        try:
            mat_id = int(str(id).replace('db-', ''))
            mat = StudyMaterial.query.get_or_404(mat_id)
            if mat.file_path and mat.file_path.startswith('static/uploads/pdfs/'):
                full_path = os.path.join(current_app.root_path, '..', mat.file_path)
                if os.path.exists(full_path):
                    try: os.remove(full_path)
                    except Exception: pass
            db.session.delete(mat)
            db.session.commit()
            flash('Uploaded PDF note deleted permanently.', 'info')
        except Exception:
            flash('Could not delete PDF note.', 'danger')
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
    text_lower = raw_text.lower()

    # 1. Company Extraction & Normalization
    company = ""
    company_id = 0
    company_logo = ""
    existing_companies = Company.query.all()
    
    matched_company = None
    for comp in existing_companies:
        if comp.name.lower() in text_lower or (comp.slug and comp.slug.lower() in text_lower):
            matched_company = comp
            break
            
    if matched_company:
        company = matched_company.name
        company_id = matched_company.id
        if matched_company.logo:
            company_logo = matched_company.logo
    else:
        comp_match = re.search(r'(?:Company|Organization|Hiring Company|Employer|Recruiter|Firm)\s*:\s*([^\n\r]+)', raw_text, re.I)
        if comp_match:
            company = comp_match.group(1).strip()
        else:
            for l in lines[:5]:
                for known in ['tcs', 'tata consultancy', 'infosys', 'accenture', 'wipro', 'deloitte', 'google', 'amazon', 'microsoft', 'capgemini', 'cognizant', 'hcl', 'tech mahindra', 'zoho', 'ibm']:
                    if known in l.lower():
                        company = l.strip()
                        break
                if company:
                    break
        company = re.sub(r'\b(is hiring|off campus|hiring drive|recruitment|drive 20\d\d)\b.*', '', company, flags=re.I).strip()

    # Logo URL extraction (only if present in raw_text or trusted company logo)
    logo_match = re.search(r'(?:Logo URL|Company Logo)\s*:\s*(https?://[^\s]+)', raw_text, re.I)
    if logo_match:
        company_logo = logo_match.group(1).strip()

    # 2. Job Title Extraction & Clean-up
    title = ""
    title_match = re.search(r'(?:Job Title|Role|Position|Designation|Post|Hiring for)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if title_match:
        title = title_match.group(1).strip()
    elif lines:
        first_line = lines[0]
        first_line = re.sub(r'^(?:TCS|Infosys|Accenture|Wipro|Deloitte|Google|Amazon|Microsoft)\s*(?:is hiring|hiring|recruitment|off campus)?\s*', '', first_line, flags=re.I).strip()
        title = first_line

    title = re.sub(r'\b(hiring|drive|20\d\d batch|off campus|freshers allowed|apply now)\b.*', '', title, flags=re.I).strip()
    if not title:
        title = lines[0] if lines else "Software Engineer"

    # 3. Category Determination (Exactly ONE of 10 allowed categories)
    category_name = "Software Development"
    category_id = 0
    
    if any(k in text_lower for k in ['intern', 'internship', 'stipend']):
        category_name = "Internships"
    elif any(k in text_lower for k in ['govt', 'government', 'public sector', 'psu', 'ssc', 'upsc', 'railway']):
        category_name = "Government Jobs"
    elif any(k in text_lower for k in ['data analyst', 'business analyst', 'bi developer', 'data analytics', 'power bi', 'tableau']):
        category_name = "Data Analytics"
    elif any(k in text_lower for k in ['data scientist', 'data science', 'machine learning', 'deep learning', 'ai engineer', 'nlp']):
        category_name = "Data Science"
    elif any(k in text_lower for k in ['devops', 'ci/cd', 'docker', 'kubernetes', 'jenkins', 'terraform']):
        category_name = "DevOps"
    elif any(k in text_lower for k in ['cloud', 'aws', 'azure', 'gcp', 'cloud engineer', 'cloud architect']):
        category_name = "Cloud"
    elif any(k in text_lower for k in ['cyber security', 'security analyst', 'soc analyst', 'penetration test', 'ethical hack']):
        category_name = "Cyber Security"
    elif any(k in text_lower for k in ['qa', 'testing', 'test engineer', 'automation tester', 'selenium']):
        category_name = "Testing"
    elif any(k in text_lower for k in ['ui/ux', 'ux designer', 'ui designer', 'figma']):
        category_name = "UI/UX"
    else:
        category_name = "Software Development"

    db_cat = Category.query.filter(Category.name.ilike(category_name)).first()
    if db_cat:
        category_id = db_cat.id

    # 4. Job Type (Full-Time, Internship, Part-Time, Contract, Walk-in Drive)
    job_type = "Full-Time"
    if any(k in text_lower for k in ['walk-in', 'walk in', 'interview drive']):
        job_type = "Walk-in Drive"
    elif any(k in text_lower for k in ['intern', 'internship', 'stipend']):
        job_type = "Internship"
    elif 'part-time' in text_lower or 'part time' in text_lower:
        job_type = "Part-Time"
    elif 'contract' in text_lower or 'temporary' in text_lower:
        job_type = "Contract"

    # 5. Work Mode (On-site, Remote, Hybrid)
    work_mode = "On-site"
    if any(k in text_lower for k in ['work from home', 'fully remote', 'remote work', 'remote']):
        work_mode = "Remote"
    elif 'hybrid' in text_lower:
        work_mode = "Hybrid"

    # 6. Location Normalization
    location = ""
    loc_match = re.search(r'(?:Location|Job Location|Work Location|Office Location|Locations)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if loc_match:
        location = loc_match.group(1).strip()
    else:
        found_locs = []
        loc_map = {
            'bangalore': 'Bengaluru, Karnataka', 'bengaluru': 'Bengaluru, Karnataka',
            'hyderabad': 'Hyderabad, Telangana', 'pune': 'Pune, Maharashtra',
            'mumbai': 'Mumbai, Maharashtra', 'chennai': 'Chennai, Tamil Nadu',
            'noida': 'Noida, Uttar Pradesh', 'gurgaon': 'Gurugram, Haryana', 'gurugram': 'Gurugram, Haryana',
            'kolkata': 'Kolkata, West Bengal', 'delhi': 'Delhi NCR', 'ahmedabad': 'Ahmedabad, Gujarat'
        }
        for k, v in loc_map.items():
            if k in text_lower and v not in found_locs:
                found_locs.append(v)
        if found_locs:
            location = ", ".join(found_locs)
        elif work_mode == "Remote":
            location = "Remote"
        else:
            location = "India"

    # 7. Educational Qualification
    qualification = ""
    qual_match = re.search(r'(?:Qualification|Education|Educational Qualification|Degree|Eligible Degrees)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if qual_match:
        qualification = qual_match.group(1).strip()
    else:
        quals = []
        for q in ['B.Tech', 'B.E', 'M.Tech', 'MCA', 'BCA', 'B.Sc', 'M.Sc', 'MBA', 'Diploma']:
            if re.search(r'\b' + re.escape(q) + r'\b', raw_text, re.I) and q not in quals:
                quals.append(q)
        if quals:
            qualification = " / ".join(quals)
        else:
            qualification = "Bachelor's degree in CS, IT, ECE, or related engineering/computer science field"

    # 8. Experience Required
    experience = ""
    exp_match = re.search(r'(?:Experience|Exp Required|Experience Level|Exp)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if exp_match:
        experience = exp_match.group(1).strip()
    else:
        num_exp = re.search(r'(\d+\s*(?:–|-|to)\s*\d+\s*(?:Years?|Yrs?))|(\d+\+?\s*(?:Years?|Yrs?))', raw_text, re.I)
        if num_exp:
            experience = num_exp.group(0).strip()
        elif 'fresher' in text_lower or '0 year' in text_lower:
            experience = "Freshers"
        else:
            experience = "Freshers"

    # 9. Key Skills (Comma separated)
    skills_list = []
    skills_match = re.search(r'(?:Skills|Key Skills|Required Skills|Technologies|Tech Stack)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if skills_match:
        skills_str = skills_match.group(1).strip()
        skills_list = [s.strip() for s in re.split(r'[,|/]', skills_str) if s.strip()]
    else:
        common_skills = ['Python', 'Java', 'C++', 'SQL', 'Data Structures', 'Algorithms', 'JavaScript', 'HTML/CSS', 'React', 'Node.js', 'AWS', 'Docker', 'Power BI', 'Excel', 'Problem Solving', 'Communication Skills']
        for s in common_skills:
            if s.lower() in text_lower:
                skills_list.append(s)
    
    if not skills_list:
        skills_list = ['Problem Solving', 'Programming Fundamentals', 'Communication Skills']
    skills = ", ".join(skills_list[:8])

    # 10. Eligibility Criteria (Bullet points)
    eligibility_bullets = []
    elig_match = re.search(r'(?:Eligibility|Eligibility Criteria|Requirements|Who Can Apply)\s*:\s*([\s\S]+?)(?=\n\s*(?:Responsibilities|Description|Skills|Salary|Location|How to Apply|Application URL)|$)', raw_text, re.I)
    if elig_match:
        raw_elig = elig_match.group(1).strip()
        for line in raw_elig.split('\n'):
            line_clean = re.sub(r'^[•\-\*\d\.\s]+', '', line).strip()
            if line_clean and len(line_clean) > 5:
                eligibility_bullets.append(f"• {line_clean}")
    
    if not eligibility_bullets:
        eligibility_bullets = [
            f"• {qualification}",
            "• Open for 2024, 2025, and 2026 graduating batches",
            "• Minimum 60% or 6.0 CGPA throughout 10th, 12th, and Graduation",
            "• No active backlogs at the time of joining",
            f"• Strong foundational knowledge in {skills}"
        ]
    eligibility = "\n".join(eligibility_bullets[:6])

    # 11. Full Job Description (Structured Bullet Points Summary)
    desc_bullets = []
    desc_match = re.search(r'(?:Job Description|About the Role|Overview|Role Overview)\s*:\s*([\s\S]+?)(?=\n\s*(?:Responsibilities|Eligibility|Skills|Qualifications|Salary|How to Apply)|$)', raw_text, re.I)
    if desc_match:
        raw_desc = desc_match.group(1).strip()
        for line in raw_desc.split('\n'):
            line_clean = re.sub(r'^[•\-\*\d\.\s]+', '', line).strip()
            if line_clean and len(line_clean) > 10:
                desc_bullets.append(f"• {line_clean}")
    
    if not desc_bullets:
        desc_bullets = [
            f"• Participate in software engineering and product development activities at {company or 'the organization'}.",
            f"• Design, build, and maintain scalable applications utilizing {skills}.",
            "• Work closely with senior technical leads, architects, and cross-functional project teams.",
            "• Perform code reviews, debugging, unit testing, and continuous quality improvement.",
            "• Adhere to modern development best practices, documentation, and agile workflows."
        ]
    description = "\n".join(desc_bullets[:6])

    # 12. Key Responsibilities (Structured Bullet Points)
    resp_bullets = []
    resp_match = re.search(r'(?:Key Responsibilities|Responsibilities|What You Will Do|Duties|Job Responsibilities)\s*:\s*([\s\S]+?)(?=\n\s*(?:Eligibility|Qualifications|Skills|Salary|How to Apply)|$)', raw_text, re.I)
    if resp_match:
        raw_resp = resp_match.group(1).strip()
        for line in raw_resp.split('\n'):
            line_clean = re.sub(r'^[•\-\*\d\.\s]+', '', line).strip()
            if line_clean and len(line_clean) > 10:
                resp_bullets.append(f"• {line_clean}")
                
    if not resp_bullets:
        resp_bullets = [
            f"• Write clean, modular, and efficient code in {skills.split(',')[0] if skills else 'core programming languages'}.",
            "• Collaborate with engineering teams to deliver features according to client & product requirements.",
            "• Conduct testing, bug fixing, and performance optimization of software modules.",
            "• Assist in technical documentation, system integration, and daily deployment pipelines."
        ]
    responsibilities = "\n".join(resp_bullets[:6])

    # 13. Salary / CTC
    salary = "Not disclosed"
    sal_match = re.search(r'(?:Salary|CTC|Stipend|Package|Pay|Compensation)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if sal_match:
        salary = sal_match.group(1).strip()
    else:
        lpa_match = re.search(r'(\b\d+(?:\.\d+)?\s*(?:–|-|to)\s*\d+(?:\.\d+)?\s*(?:LPA|Lacs|Lakhs)|₹?\s*\d+(?:\.\d+)?\s*(?:LPA|Lacs|Lakhs|k/month|per month))', raw_text, re.I)
        if lpa_match:
            salary = lpa_match.group(1).strip()
        elif 'competitive' in text_lower:
            salary = "Competitive salary"

    # 14. URLs
    urls = re.findall(r'https?://[^\s<>"]+', raw_text)
    app_url = urls[0] if urls else ""
    source_url = urls[1] if len(urls) > 1 else app_url

    # 15. Application Deadline
    deadline_str = "Not specified"
    deadline_match = re.search(r'(?:Deadline|Last Date to Apply|Apply Before|Last Date)\s*:\s*([^\n\r]+)', raw_text, re.I)
    if deadline_match:
        deadline_str = deadline_match.group(1).strip()
    else:
        d_match = re.search(r'(?:30|31|28|29|[12]?\d)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d\d', raw_text, re.I)
        if d_match:
            deadline_str = d_match.group(0).strip()

    # 16. Campus to Career Analysis Guidance
    c_title = title or "Software Engineer"
    c_comp = company or "Top Tier Employer"
    
    campus_analysis = (
        f"• Excellent entry-level opportunity for candidates aiming to build a high-growth career as {c_title} at {c_comp}.\n"
        f"• Provides hands-on exposure to production engineering workflows, team collaboration, and modern tech stacks ({skills}).\n"
        "• Great company brand value and structured learning environment for freshers and early-career job seekers."
    )
    
    who_can_apply = f"Suitable for final-year students, recent graduates (2024–2026 batches), and early-career candidates with a background in Computer Science / IT / Engineering having strong skills in {skills}."

    resume_tips = (
        f"• Highlight hands-on projects involving {skills} on the top half of page 1 of your resume.\n"
        "• Add hyperlinked URLs to your active GitHub profile and live deployed demo applications.\n"
        "• Quantify your achievements in projects (e.g. 'Optimized database queries reducing latency by 35%').\n"
        f"• Match key terms like {skills} naturally in your technical skills summary section."
    )

    interview_tips = (
        f"• Practice core Data Structures and Algorithms (Arrays, Strings, HashMaps, Recursion) in {skills.split(',')[0] if skills else 'your primary language'}.\n"
        f"• Prepare to explain your resume projects in detail, including database schema and architecture decisions.\n"
        "• Revise SQL queries (JOINs, GROUP BY, Aggregations) and Object-Oriented Programming (OOP) concepts.\n"
        "• Prepare structured answers for behavioral questions using the STAR method (Situation, Task, Action, Result)."
    )

    # 17. Missing Required Fields Detection
    missing_fields = []
    if not company:
        missing_fields.append("Company Name")
    if not app_url:
        missing_fields.append("Official Application URL")

    return jsonify({
        'company': company,
        'company_id': company_id,
        'company_logo': company_logo,
        'title': title,
        'category_name': category_name,
        'category_id': category_id,
        'qualification': qualification,
        'experience': experience,
        'salary': salary,
        'location': location,
        'work_mode': work_mode,
        'job_type': job_type,
        'skills': skills,
        'application_url': app_url,
        'source_url': source_url,
        'application_deadline_str': deadline_str,
        'description': description,
        'responsibilities': responsibilities,
        'eligibility': eligibility,
        'campus_analysis': campus_analysis,
        'who_can_apply': who_can_apply,
        'resume_tips': resume_tips,
        'interview_tips': interview_tips,
        'missing_fields': missing_fields
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
        
        raw_rows = []
        if filename.endswith('.csv'):
            file_bytes = file.stream.read()
            try:
                content = file_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                try:
                    content = file_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    content = file_bytes.decode('latin-1')
            stream = io.StringIO(content, newline=None)
            csv_reader = csv.DictReader(stream)
            raw_rows = list(csv_reader)
        elif filename.endswith('.xlsx'):
            import openpyxl
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            header = [str(cell.value or '').strip() for cell in sheet[1]]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(row):
                    raw_rows.append(dict(zip(header, row)))

        # Normalize key dictionary names
        rows_data = []
        for r in raw_rows:
            clean_r = {}
            for k, v in r.items():
                if k is not None:
                    norm_k = str(k).strip().lower().replace('\ufeff', '')
                    clean_r[norm_k] = str(v or '').strip()
            rows_data.append(clean_r)

        for idx, row in enumerate(rows_data, start=1):
            comp_name = row.get('company') or row.get('company_name') or row.get('employer') or ''
            title = row.get('title') or row.get('job_title') or row.get('position') or row.get('role') or ''
            app_url = row.get('application_url') or row.get('apply_link') or row.get('url') or row.get('link') or ''
            category_name = row.get('category') or row.get('job_category') or ''
            comp_logo = row.get('company_logo') or row.get('logo') or ''
            
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
                'location': row.get('location') or 'India',
                'experience': row.get('experience') or row.get('exp') or '0–2 Years',
                'qualification': row.get('qualification') or row.get('education') or '',
                'job_type': row.get('job_type') or row.get('type') or 'Full-Time',
                'work_mode': row.get('work_mode') or row.get('mode') or 'On-site',
                'skills': row.get('skills') or row.get('tech_stack') or '',
                'salary': row.get('salary') or row.get('ctc') or '',
                'short_description': row.get('short_description') or '',
                'description': row.get('description') or title,
                'responsibilities': row.get('responsibilities') or '',
                'eligibility': row.get('eligibility') or '',
                'application_url': app_url,
                'source_url': row.get('source_url') or '',
                'application_deadline': row.get('application_deadline') or row.get('deadline') or '',
                'youtube_url': row.get('youtube_url') or '',
                'featured': True if str(row.get('featured') or '').lower() in ['yes', 'true', '1'] else False,
                'status_val': str(row.get('status') or 'Active').capitalize(),
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
                        short_description=request.form.get(f'short_description_{i}', '')[:250],
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


