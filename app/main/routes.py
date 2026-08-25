from datetime import datetime, timedelta
import os
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, make_response, send_from_directory, abort, session, current_app
from app.extensions import db
from app.models import Job, Company, Category, DailyJobUpdate, CareerTip, Subscriber, ContactMessage, SiteSetting, StudyMaterial
from app.forms import ContactForm, SubscriberForm

main_bp = Blueprint('main', __name__)

# Dynamic NOTES_DIR resolution: static/notes inside repository first, fallback to local C:\Users\hp\Desktop\Notes
LOCAL_NOTES = r"C:\Users\hp\Desktop\Notes"
REPO_NOTES = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static', 'notes'))
NOTES_DIR = REPO_NOTES if os.path.exists(REPO_NOTES) else LOCAL_NOTES



@main_bp.route('/')
def home():
    subscriber_form = SubscriberForm()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Today's Latest Jobs (limit 4 for single row)
    today_jobs = Job.query.filter(Job.status == 'Active', Job.posted_date >= today_start)\
        .order_by(Job.posted_date.desc()).limit(4).all()
    if not today_jobs:
        today_jobs = Job.query.filter_by(status='Active')\
            .order_by(Job.posted_date.desc()).limit(4).all()

    today_job_ids = [j.id for j in today_jobs]

    # 2. Fresher Friendly Jobs (limit 4, EXCLUDING today_job_ids!)
    fresher_jobs = Job.query.filter(
        Job.status == 'Active',
        Job.id.notin_(today_job_ids),
        (Job.experience.ilike('%fresher%')) | 
        (Job.experience.ilike('%0%')) |
        (Job.experience.ilike('%1%')) |
        (Job.experience.ilike('%2%'))
    ).order_by(Job.posted_date.desc()).limit(4).all()

    if len(fresher_jobs) < 4:
        extra_ids = today_job_ids + [j.id for j in fresher_jobs]
        extra_jobs = Job.query.filter(
            Job.status == 'Active',
            Job.id.notin_(extra_ids)
        ).order_by(Job.posted_date.desc()).limit(4 - len(fresher_jobs)).all()
        fresher_jobs.extend(extra_jobs)


    # 3. Featured Companies (with active job counts)
    companies = Company.query.all()
    featured_companies_data = []
    for comp in companies:
        count = comp.jobs.filter_by(status='Active').count()
        if count > 0 or len(featured_companies_data) < 6:
            featured_companies_data.append({'company': comp, 'job_count': count})
    featured_companies_data = featured_companies_data[:6]

    # 4. Categories
    categories = Category.query.all()
    categories_data = []
    for cat in categories:
        count = cat.jobs.filter_by(status='Active').count()
        categories_data.append({'category': cat, 'job_count': count})
    categories_data.sort(key=lambda x: x['job_count'], reverse=True)

    # 5. Daily Video Update & YouTube Jobs
    latest_daily_update = DailyJobUpdate.query.order_by(DailyJobUpdate.update_date.desc()).first()
    youtube_jobs = Job.query.filter(
        Job.status == 'Active', 
        Job.youtube_video_id.isnot(None),
        Job.youtube_video_id != ''
    ).order_by(Job.posted_date.desc()).limit(4).all()

    # 6. Recent Career & Interview Tips
    recent_tips = CareerTip.query.order_by(CareerTip.created_at.desc()).limit(4).all()

    return render_template('home.html',
                           today_jobs=today_jobs,
                           fresher_jobs=fresher_jobs,
                           featured_companies_data=featured_companies_data,
                           categories_data=categories_data[:10],
                           latest_daily_update=latest_daily_update,
                           youtube_jobs=youtube_jobs,
                           recent_tips=recent_tips,
                           subscriber_form=subscriber_form,
                           title="Campus to Career | Find Jobs. Prepare Better. Get Hired.")

# --- STUDY MATERIALS & PDF NOTES LIBRARY (100% FREE DOWNLOAD) ---

def ensure_preset_notes_seeded():
    preset_data = [
        ('140 + Basic Python Programs', 'Python Notes & Coding', 'static/notes/python/140 + Basic Python Programs (1).pdf', 'bi-filetype-py', 'Complete beginner to advanced Python practice code collection.'),
        ('Python Interview Codes & Solutions', 'Python Notes & Coding', 'static/notes/python/python interview codes.pdf', 'bi-code-square', 'Handpicked Python interview coding questions with step-by-step logic.'),
        ('Project Interview Guide', 'Python Notes & Coding', 'static/notes/python/Project_Interview_Guide.pdf', 'bi-journal-code', 'How to explain Python projects in technical interviews.'),
        ('Pandas Data Analysis Notes', 'Python Notes & Coding', 'static/notes/pandas.pdf', 'bi-table', 'Comprehensive Pandas library cheat sheet & data manipulation notes.'),
        ('Java Core Complete Notes (Part 1)', 'Java & OOPs Notes', 'static/notes/java.pdf', 'bi-filetype-java', 'Fundamentals of Java programming & OOPs concepts.'),
        ('Java Advanced Notes (Part 2)', 'Java & OOPs Notes', 'static/notes/java1.pdf', 'bi-filetype-java', 'Classes, Objects, Inheritance & Interfaces in Java.'),
        ('Java Collections & Exception Notes', 'Java & OOPs Notes', 'static/notes/java2.pdf', 'bi-filetype-java', 'Lists, Sets, Maps, and Exception Handling.'),
        ('Java Master Placement Guide', 'Java & OOPs Notes', 'static/notes/Jaava4.pdf', 'bi-journal-bookmark', 'Java interview questions and placement prep notes.'),
        ('Java Conditional Statements Practice', 'Java & OOPs Notes', 'static/notes/Java_Conditional_Statements_Questions_Aligned.pdf', 'bi-check-square', 'If-else and switch-case practice problems.'),
        ('Java I/O Questions & Solutions', 'Java & OOPs Notes', 'static/notes/Java_IO_Questions.pdf', 'bi-hdd', 'File reading, writing & Scanner class questions.'),
        ('Java Looping Problems', 'Java & OOPs Notes', 'static/notes/Java_Looping_Problems.pdf', 'bi-arrow-repeat', 'For loops, while loops, and pattern printing questions.'),
        ('Java Medium to Hard Problems', 'Java & OOPs Notes', 'static/notes/Java_Problems_Medium_Hard.pdf', 'bi-exclamation-triangle', 'Advanced logic & problem solving in Java.'),
        ('Java String Problems', 'Java & OOPs Notes', 'static/notes/Java_String_Problems.pdf', 'bi-type', 'String manipulation, reversal, and substring questions.'),
        ('Master SQL Complete Notes', 'SQL & Database Notes', 'static/notes/sq/Master SQl.pdf', 'bi-database-fill', 'Complete SQL tutorial from basic SELECT to advanced JOINs.'),
        ('SQL 100 Interview Questions', 'SQL & Database Notes', 'static/notes/sq/SQL 100.pdf', 'bi-database-check', 'Top 100 SQL questions asked in technical rounds.'),
        ('SQL 45 Important Questions', 'SQL & Database Notes', 'static/notes/sq/SQL 45 questions.pdf', 'bi-database-gear', '45 high-frequency SQL problem sets with solutions.'),
        ('SQL Questions by Google', 'SQL & Database Notes', 'static/notes/sq/SQL questions by Google.pdf', 'bi-google', 'Real SQL interview problems asked in Google drives.'),
        ('SQL Placement Questions', 'SQL & Database Notes', 'static/notes/sq/SQL questions for placement .pdf', 'bi-briefcase', 'Campus placement specific SQL question bank.'),
        ('SQL Joins Master Notes', 'SQL & Database Notes', 'static/notes/sq/SQl Joins.pdf', 'bi-diagram-3-fill', 'Visual guide to INNER, LEFT, RIGHT & FULL OUTER JOINs.'),
        ('SQL Window Functions Guide', 'SQL & Database Notes', 'static/notes/sq/Window Function.pdf', 'bi-window-stack', 'ROW_NUMBER(), RANK(), DENSE_RANK(), and LEAD/LAG.'),
        ('SQL Cheat Sheet', 'SQL & Database Notes', 'static/notes/sq/sql Cheat Sheet.pdf', 'bi-file-earmark-code', 'Handy SQL syntax cheat sheet for quick revision.'),
        ('SQL Business Analyst Notes', 'SQL & Database Notes', 'static/notes/sq/sql business analsyt.pdf', 'bi-graph-up', 'Data analysis queries for Business Analyst roles.'),
        ('SQL Definitions & Theory', 'SQL & Database Notes', 'static/notes/sq/sql definitions.pdf', 'bi-book-half', 'DDL, DML, DCL, TCL, ACID properties & Normalization.'),
        ('SQL Full Notes & Queries', 'SQL & Database Notes', 'static/notes/sq/sql full notes.pdf', 'bi-file-earmark-text', 'Full handwritten SQL notes with query examples.'),
        ('MongoDB Interview Questions', 'SQL & Database Notes', 'static/notes/MongoDB_Interview_Questions.pdf', 'bi-filetype-json', 'NoSQL & MongoDB interview question bank.'),
        ('Aptitude Topics & Shortcuts', 'Aptitude & Reasoning Notes', 'static/notes/apptitude/Aptitude Topics.pdf', 'bi-calculator', 'Quantitative aptitude formulas & shortcut calculation tricks.'),
        ('Complete Placement Aptitude Guide', 'Aptitude & Reasoning Notes', 'static/notes/apptitude/topics.pdf', 'bi-puzzle', 'Comprehensive aptitude, logical & verbal reasoning notes.'),
        ('TCS NQT Complete Study Material', 'Company Specific Placement Notes', 'static/notes/Tcs NQT.pdf', 'bi-building-fill-check', 'TCS NQT exam pattern, previous papers & sample questions.'),
        ('Deloitte Placement Guide', 'Company Specific Placement Notes', 'static/notes/Deloitee.pdf', 'bi-building', 'Deloitte Analyst interview questions & test syllabus.'),
        ('Cognizant Data Analyst Material', 'Company Specific Placement Notes', 'static/notes/Cognizant Data analyst.pdf', 'bi-file-earmark-bar-graph', 'Cognizant Data Analyst test pattern & preparation notes.'),
        ('Cognizant 2025 Interview Questions', 'Company Specific Placement Notes', 'static/notes/Cognizant_Interview_Questions_2025.pdf', 'bi-question-circle', 'Recent Cognizant interview questions.'),
        ('Data Structures & Algorithms (DSA)', 'Company Specific Placement Notes', 'static/notes/DSA.pdf', 'bi-diagram-2', 'Complete DSA notes covering Trees, Graphs & Dynamic Programming.'),
        ('Power BI Master Notes', 'Data Science & Power BI Notes', 'static/notes/Power bi.pdf', 'bi-bar-chart-line-fill', 'Complete Power BI visual dashboards & DAX formulas.'),
        ('Power BI Interview QnA', 'Data Science & Power BI Notes', 'static/notes/Power_BI_interview_QnA[1].pdf', 'bi-file-earmark-easel', 'Top Power BI interview questions & answers.'),
        ('Myntra Data Analyst Interview Questions', 'Data Science & Power BI Notes', 'static/notes/Myntra Data Analyst Interview.pdf', 'bi-bag-check', 'Real Myntra Data Analyst interview case studies.'),
        ('Roadmap for Data Analyst Career', 'Data Science & Power BI Notes', 'static/notes/Roadmap for data analysis.pdf', 'bi-signpost-split', 'Step-by-step career path to become a Data Analyst.'),
        ('AWS Cloud Practitioner Guide', 'Data Science & Power BI Notes', 'static/notes/aws.pdf', 'bi-cloud-check', 'AWS cloud services, S3, EC2 & certification basics.')
    ]
    for title, cat, path, icon, desc in preset_data:
        existing = StudyMaterial.query.filter(StudyMaterial.title.ilike(title)).first()
        if not existing:
            slug = generate_unique_slug(StudyMaterial, title)
            mat = StudyMaterial(
                title=title,
                slug=slug,
                category=cat,
                description=desc,
                file_path=path,
                icon=icon
            )
            db.session.add(mat)
    db.session.commit()

@main_bp.route('/study-materials')
def study_materials():
    ensure_preset_notes_seeded()
    db_materials = StudyMaterial.query.order_by(StudyMaterial.created_at.desc()).all()
    
    categories = {}
    for mat in db_materials:
        cat_name = mat.category or 'General Placement Notes'
        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append({
            'id': f'db-{mat.id}',
            'name': mat.title,
            'file': f'db:{mat.id}',
            'icon': mat.icon or 'bi-file-earmark-pdf',
            'desc': mat.description or 'PDF Note Document'
        })

    return render_template('pages/study_materials.html', 
                           categories=categories,
                           title="PDF Notes & Study Material Library - Campus to Career")


@main_bp.route('/notes/download/<path:filename>')
def download_note(filename):
    if filename.startswith('db:'):
        mat_id = int(filename.split(':')[1])
        mat = StudyMaterial.query.get_or_404(mat_id)
        mat.download_count += 1
        db.session.commit()
        
        full_path = os.path.normpath(os.path.abspath(os.path.join(current_app.root_path, '..', mat.file_path)))
        if not os.path.exists(full_path):
            target_file_name = os.path.basename(mat.file_path)
            found = False
            notes_root = os.path.normpath(os.path.abspath(os.path.join(current_app.root_path, '..', 'static', 'notes')))
            if os.path.exists(notes_root):
                for root, dirs, files in os.walk(notes_root):
                    if target_file_name in files:
                        full_path = os.path.join(root, target_file_name)
                        found = True
                        break
            if not found:
                abort(404)
        resp = send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), as_attachment=False, mimetype='application/pdf')
        resp.headers['Content-Disposition'] = f'inline; filename="{os.path.basename(full_path)}"'
        return resp

    target_dir = REPO_NOTES if os.path.exists(REPO_NOTES) else LOCAL_NOTES
    file_path = os.path.join(target_dir, filename)
    if not os.path.isfile(file_path):
        # Fallback check directly inside project root static/notes
        alt_path = os.path.abspath(os.path.join(current_app.root_path, '..', 'static', 'notes', filename))
        if os.path.isfile(alt_path):
            file_path = alt_path
        else:
            abort(404)

    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    resp = send_from_directory(directory, base_name, as_attachment=False, mimetype='application/pdf')
    resp.headers['Content-Disposition'] = f'inline; filename="{base_name}"'
    return resp



@main_bp.route('/subscribe', methods=['POST'])
def subscribe():
    form = SubscriberForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing = Subscriber.query.filter_by(email=email).first()
        if existing:
            if not existing.is_active:
                existing.is_active = True
                db.session.commit()
                flash('Welcome back! Your subscription has been reactivated.', 'success')
            else:
                flash('You are already subscribed to daily job updates!', 'info')
        else:
            new_sub = Subscriber(email=email)
            db.session.add(new_sub)
            db.session.commit()
            flash('Thank you for subscribing! You will receive daily job notifications.', 'success')
    else:
        flash('Please provide a valid email address.', 'danger')
        
    return redirect(request.referrer or url_for('main.home'))

@main_bp.route('/daily-jobs/<slug>')
def daily_job_update(slug):
    update = DailyJobUpdate.query.filter_by(slug=slug).first_or_404()
    jobs = update.jobs.filter(Job.status.in_(['Active', 'Expired'])).all()
    return render_template('daily_jobs.html', update=update, jobs=jobs, title=f"{update.title} - Campus to Career")

@main_bp.route('/career-tips')
def career_tips():
    category_filter = request.args.get('category', '').strip()
    query = CareerTip.query
    if category_filter:
        query = query.filter_by(category=category_filter)
    tips = query.order_by(CareerTip.created_at.desc()).all()
    return render_template('career_tips/index.html', tips=tips, category_filter=category_filter, title="Interview Preparation & Coding Materials - Campus to Career")

@main_bp.route('/career-tips/<slug>')
def career_tip_detail(slug):
    tip = CareerTip.query.filter_by(slug=slug).first_or_404()
    related_jobs = Job.query.filter_by(status='Active').order_by(Job.posted_date.desc()).limit(4).all()
    return render_template('career_tips/detail.html', tip=tip, related_jobs=related_jobs, title=f"{tip.title} - Campus to Career")

@main_bp.route('/about')
def about():
    return render_template('pages/about.html', title='About Us - Campus to Career')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            subject=form.subject.data.strip(),
            message=form.message.data.strip()
        )
        db.session.add(msg)
        db.session.commit()
        flash('Thank you for contacting us! We will get back to you shortly.', 'success')
        return redirect(url_for('main.contact'))
        
    return render_template('pages/contact.html', form=form, title='Contact Us - Campus to Career')

@main_bp.route('/privacy-policy')
def privacy():
    return render_template('pages/privacy.html', title='Privacy Policy - Campus to Career')

@main_bp.route('/terms')
def terms():
    return render_template('pages/terms.html', title='Terms & Conditions - Campus to Career')

@main_bp.route('/disclaimer')
def disclaimer():
    return render_template('pages/disclaimer.html', title='Disclaimer - Campus to Career')

@main_bp.route('/editorial-policy')
def editorial():
    return render_template('pages/editorial.html', title='Editorial Policy - Campus to Career')

@main_bp.route('/robots.txt')
def robots():
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/

Sitemap: {}/sitemap.xml
""".format(request.host_url.rstrip('/'))
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain'
    return response

@main_bp.route('/sitemap.xml')
def sitemap():
    jobs = Job.query.filter_by(status='Active').all()
    companies = Company.query.all()
    categories = Category.query.all()
    daily_updates = DailyJobUpdate.query.all()
    tips = CareerTip.query.all()
    
    xml = render_template('sitemap.xml', 
                          jobs=jobs, 
                          companies=companies, 
                          categories=categories,
                          daily_updates=daily_updates,
                          tips=tips,
                          base_url=request.host_url.rstrip('/'))
    response = make_response(xml)
    response.headers['Content-Type'] = 'application/xml'
    return response
