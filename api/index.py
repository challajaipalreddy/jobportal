import os
import sys

# Add project root directory to sys.path
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, basedir)

from app import create_app

app = create_app('production')

@app.before_request
def init_db_once():
    if not getattr(app, '_db_initialized', False):
        try:
            from app.extensions import db
            from app.models import User
            db.create_all()
            if not User.query.filter_by(email='admin@campustocareer.com').first():
                admin = User(username='admin', email='admin@campustocareer.com', is_admin=True)
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
            app._db_initialized = True
        except Exception as err:
            print("Vercel DB Init Notice:", err)
