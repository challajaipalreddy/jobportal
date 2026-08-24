from datetime import datetime
from flask import Blueprint, render_template, request, abort, make_response
from sqlalchemy import or_
from app.extensions import db
from app.models import Job, Company, Category

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/jobs')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Query parameters
    keyword = request.args.get('q', '').strip()
    company_id = request.args.get('company', type=int)
    category_id = request.args.get('category', type=int)
    location = request.args.get('location', '').strip()
    job_type = request.args.get('job_type', '').strip()
    work_mode = request.args.get('work_mode', '').strip()
    experience = request.args.get('experience', '').strip()
    is_fresher = request.args.get('fresher', type=int)
    is_internship = request.args.get('internship', type=int)
    sort_by = request.args.get('sort', 'latest').strip()

    # Base query: Only show Active jobs to public, or expired if specified
    query = Job.query.filter(Job.status.in_(['Active', 'Expired']))

    # Keyword search across title, skills, description, eligibility, responsibilities
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.skills.ilike(search_pattern),
                Job.description.ilike(search_pattern),
                Job.responsibilities.ilike(search_pattern),
                Job.qualification.ilike(search_pattern),
                Job.eligibility.ilike(search_pattern)
            )
        )

    if company_id:
        query = query.filter(Job.company_id == company_id)

    if category_id:
        query = query.filter(Job.category_id == category_id)

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if job_type:
        query = query.filter(Job.job_type == job_type)

    if work_mode:
        query = query.filter(Job.work_mode == work_mode)

    if experience:
        query = query.filter(Job.experience.ilike(f"%{experience}%"))

    if is_fresher:
        query = query.filter(or_(Job.experience.ilike("%0%"), Job.experience.ilike("%fresher%")))

    if is_internship:
        query = query.filter(Job.job_type == 'Internship')

    # Sorting
    if sort_by == 'oldest':
        query = query.order_by(Job.posted_date.asc())
    elif sort_by == 'deadline':
        query = query.order_by(Job.application_deadline.asc().nullslast())
    elif sort_by == 'views':
        query = query.order_by(Job.views.desc())
    else:  # 'latest'
        query = query.order_by(Job.posted_date.desc())

    paginated_jobs = query.paginate(page=page, per_page=per_page, error_out=False)

    companies = Company.query.order_by(Company.name.asc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template('jobs/index.html',
                           jobs=paginated_jobs.items,
                           pagination=paginated_jobs,
                           companies=companies,
                           categories=categories,
                           current_keyword=keyword,
                           current_company=company_id,
                           current_category=category_id,
                           current_location=location,
                           current_job_type=job_type,
                           current_work_mode=work_mode,
                           current_sort=sort_by,
                           title="Browse Jobs & Placement Drives - Campus to Career")

@jobs_bp.route('/jobs/<slug>')
def detail(slug):
    job = Job.query.filter_by(slug=slug).first_or_404()
    
    # Handle view count tracking with cookie check to avoid duplicate counts on page refresh
    view_cookie_name = f'viewed_job_{job.id}'
    has_viewed = request.cookies.get(view_cookie_name)
    
    if not has_viewed:
        job.views = (job.views or 0) + 1
        db.session.commit()
    
    # Check if job is expired automatically if deadline passed
    is_job_expired = job.is_expired()
    
    # Similar / Related jobs
    related_jobs = Job.query.filter(
        Job.id != job.id,
        Job.status == 'Active',
        or_(Job.category_id == job.category_id, Job.company_id == job.company_id)
    ).order_by(Job.posted_date.desc()).limit(4).all()

    # Dynamic SEO Metadata
    seo_title = job.seo_title or f"{job.company.name} {job.title} - Campus to Career"
    seo_description = job.seo_description or (job.short_description[:150] if job.short_description else f"Apply for {job.title} at {job.company.name}. Check eligibility, qualification, skills and apply link.")
    
    resp = make_response(render_template(
        'jobs/detail.html',
        job=job,
        is_job_expired=is_job_expired,
        related_jobs=related_jobs,
        seo_title=seo_title,
        seo_description=seo_description,
        title=seo_title
    ))
    
    if not has_viewed:
        # Set cookie for 2 hours
        resp.set_cookie(view_cookie_name, '1', max_age=7200)
        
    return resp
