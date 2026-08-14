from app import create_app, db
from app.models import User

app = create_app('production')

with app.app_context():
    try:
        db.create_all()
        if not User.query.filter_by(email='admin@campustocareer.com').first():
            admin = User(username='admin', email='admin@campustocareer.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    except Exception as e:
        print("DB Init Notice:", e)

if __name__ == '__main__':
    app.run()
