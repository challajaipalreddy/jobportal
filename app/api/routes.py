from flask import Blueprint, jsonify, request
from app.models import Job, Company, Category

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/jobs')
def get_jobs():
    category_slug = request.args.get('category')
    company_slug = request.args.get('company')
    limit = request.args.get('limit', 10, type=int)

    query = Job.query.filter_by(status='Active')

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if company_slug:
        comp = Company.query.filter_by(slug=company_slug).first()
        if comp:
            query = query.filter_by(company_id=comp.id)

    jobs = query.order_by(Job.posted_date.desc()).limit(limit).all()

    data = []
    for j in jobs:
        data.append({
            'id': j.id,
            'title': j.title,
            'slug': j.slug,
            'company': j.company.name,
            'company_logo': j.company.logo,
            'location': j.location,
            'experience': j.experience,
            'job_type': j.job_type,
            'work_mode': j.work_mode,
            'salary': j.salary,
            'posted_date': j.posted_date.strftime('%Y-%m-%d'),
            'application_url': j.application_url,
            'youtube_video_url': j.youtube_video_url,
            'youtube_thumbnail': j.youtube_thumbnail
        })

    return jsonify({'success': True, 'count': len(data), 'jobs': data})

@api_bp.route('/jobs/<slug>')
def get_job_detail(slug):
    job = Job.query.filter_by(slug=slug).first()
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'}), 404

    return jsonify({
        'success': True,
        'job': {
            'id': job.id,
            'title': job.title,
            'slug': job.slug,
            'company': {
                'name': job.company.name,
                'slug': job.company.slug,
                'logo': job.company.logo,
                'website': job.company.website
            },
            'category': job.category.name if job.category else None,
            'job_type': job.job_type,
            'work_mode': job.work_mode,
            'location': job.location,
            'qualification': job.qualification,
            'experience': job.experience,
            'skills': job.skills,
            'salary': job.salary,
            'short_description': job.short_description,
            'description': job.description,
            'responsibilities': job.responsibilities,
            'eligibility': job.eligibility,
            'campus_analysis': job.campus_analysis,
            'who_can_apply': job.who_can_apply,
            'application_url': job.application_url,
            'posted_date': job.posted_date.isoformat(),
            'application_deadline': job.application_deadline.isoformat() if job.application_deadline else None,
            'youtube_video_url': job.youtube_video_url,
            'youtube_video_id': job.youtube_video_id,
            'views': job.views
        }
    })

@api_bp.route('/categories')
def get_categories():
    categories = Category.query.all()
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug, 'icon': c.icon} for c in categories]
    return jsonify({'success': True, 'categories': data})

@api_bp.route('/companies')
def get_companies():
    companies = Company.query.all()
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug, 'logo': c.logo, 'website': c.website} for c in companies]
    return jsonify({'success': True, 'companies': data})

@api_bp.route('/health')
def health_check():
    from datetime import datetime
    return jsonify({
        'status': 'online',
        'service': 'Campus to Career Hub',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_status': 'active'
    }), 200

