import os
from app import create_app, db
from app.models import Job, Company, Category
from app.utils import generate_unique_slug
from app.live_jobs_sync import sync_live_jobs

env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

with app.app_context():
    try:
        db.create_all()
        sync_live_jobs(app, db, Job, Company, Category, generate_unique_slug)
    except Exception as e:
        print("Run startup sync notice:", e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
