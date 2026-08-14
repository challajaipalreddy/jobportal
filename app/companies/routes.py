from flask import Blueprint, render_template, request
from app.models import Company, Job

companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/companies')
def index():
    page = request.args.get('page', 1, type=int)
    search_q = request.args.get('q', '').strip()
    
    query = Company.query
    if search_q:
        query = query.filter(Company.name.ilike(f"%{search_q}%"))
        
    query = query.order_by(Company.name.asc())
    paginated = query.paginate(page=page, per_page=16, error_out=False)
    
    return render_template('companies/index.html',
                           companies=paginated.items,
                           pagination=paginated,
                           search_q=search_q,
                           title="Top Hiring Companies - Campus to Career")

@companies_bp.route('/companies/<slug>')
def detail(slug):
    company = Company.query.filter_by(slug=slug).first_or_404()
    
    # Active jobs & internships
    active_jobs = Job.query.filter_by(company_id=company.id, status='Active')\
        .order_by(Job.posted_date.desc()).all()
        
    return render_template('companies/detail.html',
                           company=company,
                           jobs=active_jobs,
                           title=f"{company.name} Jobs, Internships & Careers - Campus to Career")
