from datetime import datetime, timedelta
import os
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, make_response, send_from_directory, abort, session, current_app
from app.extensions import db
from app.models import Job, Company, Category, DailyJobUpdate, CareerTip, Subscriber, ContactMessage, SiteSetting, StudyMaterial
from app.forms import ContactForm, SubscriberForm

main_bp = Blueprint('main', __name__)

NOTES_DIR = r"C:\Users\hp\Desktop\Notes"

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

@main_bp.route('/study-materials')
def study_materials():
    db_materials = StudyMaterial.query.order_by(StudyMaterial.created_at.desc()).all()
    
    # Preset notes from local Notes folder
    preset_categories = {
        'Python Notes & Coding': [
            {'id': 'preset-1', 'name': '140 + Basic Python Programs', 'file': 'python/140 + Basic Python Programs (1).pdf', 'icon': 'bi-filetype-py', 'desc': 'Complete beginner to advanced Python practice code collection.'},
            {'id': 'preset-2', 'name': 'Python Interview Codes & Solutions', 'file': 'python/python interview codes.pdf', 'icon': 'bi-code-square', 'desc': 'Handpicked Python interview coding questions with step-by-step logic.'},
            {'id': 'preset-3', 'name': 'Project Interview Guide', 'file': 'python/Project_Interview_Guide.pdf', 'icon': 'bi-journal-code', 'desc': 'How to explain Python projects in technical interviews.'},
            {'id': 'preset-4', 'name': 'Pandas Data Analysis Notes', 'file': 'pandas.pdf', 'icon': 'bi-table', 'desc': 'Comprehensive Pandas library cheat sheet & data manipulation notes.'}
        ],
        'Java & OOPs Notes': [
            {'id': 'preset-5', 'name': 'Java Core Complete Notes (Part 1)', 'file': 'java.pdf', 'icon': 'bi-filetype-java', 'desc': 'Fundamentals of Java programming & OOPs concepts.'},
            {'id': 'preset-6', 'name': 'Java Advanced Notes (Part 2)', 'file': 'java1.pdf', 'icon': 'bi-filetype-java', 'desc': 'Classes, Objects, Inheritance & Interfaces in Java.'},
            {'id': 'preset-7', 'name': 'Java Collections & Exception Notes', 'file': 'java2.pdf', 'icon': 'bi-filetype-java', 'desc': 'Lists, Sets, Maps, and Exception Handling.'},
            {'id': 'preset-8', 'name': 'Java Master Placement Guide', 'file': 'Jaava4.pdf', 'icon': 'bi-journal-bookmark', 'desc': 'Java interview questions and placement prep notes.'},
            {'id': 'preset-9', 'name': 'Java Conditional Statements Practice', 'file': 'Java_Conditional_Statements_Questions_Aligned.pdf', 'icon': 'bi-check-square', 'desc': 'If-else and switch-case practice problems.'},
            {'id': 'preset-10', 'name': 'Java I/O Questions & Solutions', 'file': 'Java_IO_Questions.pdf', 'icon': 'bi-hdd', 'desc': 'File reading, writing & Scanner class questions.'},
            {'id': 'preset-11', 'name': 'Java Looping Problems', 'file': 'Java_Looping_Problems.pdf', 'icon': 'bi-arrow-repeat', 'desc': 'For loops, while loops, and pattern printing questions.'},
            {'id': 'preset-12', 'name': 'Java Medium to Hard Problems', 'file': 'Java_Problems_Medium_Hard.pdf', 'icon': 'bi-exclamation-triangle', 'desc': 'Advanced logic & problem solving in Java.'},
            {'id': 'preset-13', 'name': 'Java String Problems', 'file': 'Java_String_Problems.pdf', 'icon': 'bi-type', 'desc': 'String manipulation, reversal, and substring questions.'}
        ],
        'SQL & Database Notes': [
            {'id': 'preset-14', 'name': 'Master SQL Complete Notes', 'file': 'sq/Master SQl.pdf', 'icon': 'bi-database-fill', 'desc': 'Complete SQL tutorial from basic SELECT to advanced JOINs.'},
            {'id': 'preset-15', 'name': 'SQL 100 Interview Questions', 'file': 'sq/SQL 100.pdf', 'icon': 'bi-database-check', 'desc': 'Top 100 SQL questions asked in technical rounds.'},
            {'id': 'preset-16', 'name': 'SQL 45 Important Questions', 'file': 'sq/SQL 45 questions.pdf', 'icon': 'bi-database-gear', 'desc': '45 high-frequency SQL problem sets with solutions.'},
            {'id': 'preset-17', 'name': 'SQL Questions by Google', 'file': 'sq/SQL questions by Google.pdf', 'icon': 'bi-google', 'desc': 'Real SQL interview problems asked in Google drives.'},
            {'id': 'preset-18', 'name': 'SQL Placement Questions', 'file': 'sq/SQL questions for placement .pdf', 'icon': 'bi-briefcase', 'desc': 'Campus placement specific SQL question bank.'},
            {'id': 'preset-19', 'name': 'SQL Joins Master Notes', 'file': 'sq/SQl Joins.pdf', 'icon': 'bi-diagram-3-fill', 'desc': 'Visual guide to INNER, LEFT, RIGHT & FULL OUTER JOINs.'},
            {'id': 'preset-20', 'name': 'SQL Window Functions Guide', 'file': 'sq/Window Function.pdf', 'icon': 'bi-window-stack', 'desc': 'ROW_NUMBER(), RANK(), DENSE_RANK(), and LEAD/LAG.'},
            {'id': 'preset-21', 'name': 'SQL Cheat Sheet', 'file': 'sq/sql Cheat Sheet.pdf', 'icon': 'bi-file-earmark-code', 'desc': 'Handy SQL syntax cheat sheet for quick revision.'},
            {'id': 'preset-22', 'name': 'SQL Business Analyst Notes', 'file': 'sq/sql business analsyt.pdf', 'icon': 'bi-graph-up', 'desc': 'Data analysis queries for Business Analyst roles.'},
            {'id': 'preset-23', 'name': 'SQL Definitions & Theory', 'file': 'sq/sql definitions.pdf', 'icon': 'bi-book-half', 'desc': 'DDL, DML, DCL, TCL, ACID properties & Normalization.'},
            {'id': 'preset-24', 'name': 'SQL Full Notes & Queries', 'file': 'sq/sql full notes.pdf', 'icon': 'bi-file-earmark-text', 'desc': 'Full handwritten SQL notes with query examples.'},
            {'id': 'preset-25', 'name': 'MongoDB Interview Questions', 'file': 'MongoDB_Interview_Questions.pdf', 'icon': 'bi-filetype-json', 'desc': 'NoSQL & MongoDB interview question bank.'}
        ],
        'Aptitude & Reasoning Notes': [
            {'id': 'preset-26', 'name': 'Aptitude Topics & Shortcuts', 'file': 'apptitude/Aptitude Topics.pdf', 'icon': 'bi-calculator', 'desc': 'Quantitative aptitude formulas & shortcut calculation tricks.'},
            {'id': 'preset-27', 'name': 'Complete Placement Aptitude Guide', 'file': 'apptitude/topics.pdf', 'icon': 'bi-puzzle', 'desc': 'Comprehensive aptitude, logical & verbal reasoning notes.'}
        ],
        'Company Specific Placement Notes': [
            {'id': 'preset-28', 'name': 'TCS NQT Complete Study Material', 'file': 'Tcs NQT.pdf', 'icon': 'bi-building-fill-check', 'desc': 'TCS NQT exam pattern, previous papers & sample questions.'},
            {'id': 'preset-29', 'name': 'Deloitte Placement Guide', 'file': 'Deloitee.pdf', 'icon': 'bi-building', 'desc': 'Deloitte Analyst interview questions & test syllabus.'},
            {'id': 'preset-30', 'name': 'Cognizant Data Analyst Material', 'file': 'Cognizant Data analyst.pdf', 'icon': 'bi-file-earmark-bar-graph', 'desc': 'Cognizant Data Analyst test pattern & preparation notes.'},
            {'id': 'preset-31', 'name': 'Cognizant 2025 Interview Questions', 'file': 'Cognizant_Interview_Questions_2025.pdf', 'icon': 'bi-question-circle', 'desc': 'Recent Cognizant interview questions.'},
            {'id': 'preset-32', 'name': 'Data Structures & Algorithms (DSA)', 'file': 'DSA.pdf', 'icon': 'bi-diagram-2', 'desc': 'Complete DSA notes covering Trees, Graphs & Dynamic Programming.'}
        ],
        'Data Science & Power BI Notes': [
            {'id': 'preset-33', 'name': 'Power BI Master Notes', 'file': 'Power bi.pdf', 'icon': 'bi-bar-chart-line-fill', 'desc': 'Complete Power BI visual dashboards & DAX formulas.'},
            {'id': 'preset-34', 'name': 'Power BI Interview QnA', 'file': 'Power_BI_interview_QnA[1].pdf', 'icon': 'bi-file-earmark-easel', 'desc': 'Top Power BI interview questions & answers.'},
            {'id': 'preset-35', 'name': 'Myntra Data Analyst Interview Questions', 'file': 'Myntra Data Analyst Interview.pdf', 'icon': 'bi-bag-check', 'desc': 'Real Myntra Data Analyst interview case studies.'},
            {'id': 'preset-36', 'name': 'Roadmap for Data Analyst Career', 'file': 'Roadmap for data analysis.pdf', 'icon': 'bi-signpost-split', 'desc': 'Step-by-step career path to become a Data Analyst.'},
            {'id': 'preset-37', 'name': 'AWS Cloud Practitioner Guide', 'file': 'aws.pdf', 'icon': 'bi-cloud-check', 'desc': 'AWS cloud services, S3, EC2 & certification basics.'}
        ]
    }

    # Add custom uploaded DB materials to categories
    for mat in db_materials:
        cat_name = mat.category
        if cat_name not in preset_categories:
            preset_categories[cat_name] = []
        preset_categories[cat_name].insert(0, {
            'id': f'db-{mat.id}',
            'name': mat.title,
            'file': f'db:{mat.id}',
            'icon': mat.icon or 'bi-file-earmark-pdf',
            'desc': mat.description or 'Uploaded PDF Note'
        })

    return render_template('pages/study_materials.html', 
                           categories=preset_categories,
                           title="PDF Notes & Study Material Library - Campus to Career")

@main_bp.route('/notes/download/<path:filename>')
def download_note(filename):
    if filename.startswith('db:'):
        mat_id = int(filename.split(':')[1])
        mat = StudyMaterial.query.get_or_404(mat_id)
        mat.download_count += 1
        db.session.commit()
        full_path = os.path.join(current_app.root_path, '..', mat.file_path)
        if not os.path.exists(full_path):
            abort(404)
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), as_attachment=False)

    if not os.path.exists(NOTES_DIR):
        abort(404)
    file_path = os.path.join(NOTES_DIR, filename)
    if not os.path.isfile(file_path):
        abort(404)

    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    return send_from_directory(directory, base_name, as_attachment=False)

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
