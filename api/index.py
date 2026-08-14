import os
import sys

# Append project root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Category, Job, Company, StudyMaterial, DailyJobUpdate, CareerTip, Subscriber, ContactMessage, SiteSetting

app = create_app('production')

with app.app_context():
    try:
        db.create_all()
        # Seed initial admin user if missing
        if not User.query.filter_by(email='admin@campustocareer.com').first():
            admin = User(username='admin', email='admin@campustocareer.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    except Exception as e:
        print("Vercel DB Init Notice:", e)

# Export WSGI application handler for Vercel
app = app
