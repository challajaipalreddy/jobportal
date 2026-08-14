import os
import re
from flask import Flask, render_template
from config import config_by_name
from app.extensions import db, login_manager

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.jobs.routes import jobs_bp
    from app.companies.routes import companies_bp
    from app.categories.routes import categories_bp
    from app.internships.routes import internships_bp
    from app.admin.routes import admin_bp
    from app.api.routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(internships_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Global Jinja context processors & filters
    @app.context_processor
    def inject_global_data():
        top_categories = []
        try:
            from app.models import Category
            top_categories = Category.query.limit(6).all()
        except Exception:
            top_categories = []

        return dict(
            top_categories=top_categories,
            now=os.environ.get('CURRENT_TIME', '2026')
        )

    # Custom Jinja filters
    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        if not dt:
            return ''
        from datetime import datetime
        now = datetime.utcnow()
        diff = now - dt
        if diff.days == 0:
            if diff.seconds < 3600:
                mins = diff.seconds // 60
                return f"{mins}m ago" if mins > 0 else "Just now"
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 30:
            return f"{diff.days} days ago"
        else:
            return dt.strftime('%b %d, %Y')

    @app.template_filter('markdown_to_html')
    def markdown_to_html_filter(text):
        if not text:
            return ''
        try:
            import markdown
            html = markdown.markdown(text, extensions=['fenced_code', 'tables'])
            # Transform <a> links into styled clickable buttons
            html = re.sub(
                r'<a href="([^"]+)">([^<]+)</a>',
                r'<a href="\1" target="_blank" rel="noopener noreferrer" class="btn btn-outline-primary btn-sm my-1 me-1 shadow-sm"><i class="bi bi-box-arrow-up-right me-1"></i> \2</a>',
                html
            )
            return html
        except ImportError:
            # Fallback regex parser for [text](url) markdown syntax
            out = text
            out = re.sub(r'###\s*(.+)', r'<h5 class="fw-bold mt-4 mb-2">\1</h5>', out)
            out = re.sub(r'####\s*(.+)', r'<h6 class="fw-bold mt-3 mb-2 text-primary">\1</h6>', out)
            out = re.sub(
                r'\[(.*?)\]\((.*?)\)',
                r'<a href="\2" target="_blank" rel="noopener noreferrer" class="btn btn-outline-primary btn-sm my-1 me-1 shadow-sm"><i class="bi bi-box-arrow-up-right me-1"></i> \1</a>',
                out
            )
            return out.replace('\n', '<br>')

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html', title='Opportunity Not Found - Campus to Career'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html', title='Server Error - Campus to Career'), 500

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app

# Expose 'app' instance at module level so 'gunicorn app:app' works on Render/production WSGI
app = create_app(os.environ.get('FLASK_ENV', 'production'))

with app.app_context():
    try:
        db.create_all()
        from app.models import Category, User
        if not Category.query.first():
            from seed import seed_database
            seed_database()

        # Guarantee admin user 'admin' exists with password 'admin123'
        admin = User.query.filter_by(email='admin@campustocareer.com').first()
        if not admin:
            admin = User(username='admin', email='admin@campustocareer.com', is_admin=True)
            db.session.add(admin)
        admin.set_password('admin123')
        admin.is_admin = True

        # Guarantee admin user 'jaireddy' exists with password 'jaireddy@12'
        jai = User.query.filter((User.username == 'jaireddy') | (User.email == 'jaireddy@campustocareer.com')).first()
        if not jai:
            jai = User(username='jaireddy', email='jaireddy@campustocareer.com', is_admin=True)
            db.session.add(jai)
        jai.set_password('jaireddy@12')
        jai.is_admin = True
        
        db.session.commit()

    except Exception as err:
        print("Auto DB initialization notice:", err)

