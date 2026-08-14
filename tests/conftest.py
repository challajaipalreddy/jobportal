import pytest
from app import create_app, db
from app.models import User, Company, Category, Job

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        
        # Seed test admin
        admin = User(username='testadmin', email='testadmin@test.com', is_admin=True)
        admin.set_password('TestPass123!')
        db.session.add(admin)

        # Seed test company & category
        comp = Company(name='Test Company', slug='test-company')
        cat = Category(name='Test Category', slug='test-category')
        db.session.add(comp)
        db.session.add(cat)
        db.session.commit()

        # Seed test job
        job = Job(
            title='Test Engineer',
            slug='test-engineer',
            company_id=comp.id,
            category_id=cat.id,
            description='Full description for testing engineer role.',
            application_url='https://example.com/apply',
            status='Active',
            youtube_video_id='dQw4w9WgXcQ'
        )
        db.session.add(job)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    client.post('/admin/login', data={
        'email': 'testadmin@test.com',
        'password': 'TestPass123!'
    }, follow_redirects=True)
    return client
