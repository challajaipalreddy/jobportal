from flask import Blueprint, render_template, request
from app.models import Category, Job

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/category/<slug>')
def detail(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    query = Job.query.filter_by(category_id=category.id, status='Active')\
        .order_by(Job.posted_date.desc())
        
    paginated = query.paginate(page=page, per_page=12, error_out=False)
    
    return render_template('categories/detail.html',
                           category=category,
                           jobs=paginated.items,
                           pagination=paginated,
                           title=f"{category.name} Jobs for Freshers & Students - Campus to Career")
