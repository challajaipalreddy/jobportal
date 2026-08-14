from flask import Blueprint, render_template, request
from sqlalchemy import or_
from app.models import Job, Company, Category

internships_bp = Blueprint('internships', __name__)

@internships_bp.route('/internships')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    keyword = request.args.get('q', '').strip()
    company_id = request.args.get('company', type=int)
    work_mode = request.args.get('work_mode', '').strip()
    location = request.args.get('location', '').strip()
    
    query = Job.query.filter(
        Job.status.in_(['Active', 'Expired']),
        Job.job_type == 'Internship'
    )
    
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.skills.ilike(search_pattern),
                Job.description.ilike(search_pattern),
                Job.qualification.ilike(search_pattern)
            )
        )
        
    if company_id:
        query = query.filter(Job.company_id == company_id)
        
    if work_mode:
        query = query.filter(Job.work_mode == work_mode)
        
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
        
    query = query.order_by(Job.posted_date.desc())
    paginated_internships = query.paginate(page=page, per_page=per_page, error_out=False)
    
    companies = Company.query.order_by(Company.name.asc()).all()

    return render_template('internships/index.html',
                           internships=paginated_internships.items,
                           pagination=paginated_internships,
                           companies=companies,
                           current_keyword=keyword,
                           current_company=company_id,
                           current_work_mode=work_mode,
                           current_location=location,
                           title="Latest Internships for Students & Freshers - Campus to Career")
