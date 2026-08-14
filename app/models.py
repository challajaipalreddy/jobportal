from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    logo = db.Column(db.String(500), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs = db.relationship('Job', backref='company', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Company {self.name}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True, default='bi-briefcase')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobs = db.relationship('Job', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

class DailyJobUpdate(db.Model):
    __tablename__ = 'daily_job_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    update_date = db.Column(db.Date, nullable=False, index=True)
    youtube_video_url = db.Column(db.String(255), nullable=True)
    youtube_video_id = db.Column(db.String(50), nullable=True)
    youtube_description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobs = db.relationship('Job', backref='daily_update', lazy='dynamic')

    def __repr__(self):
        return f'<DailyJobUpdate {self.title}>'

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(250), unique=True, nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)
    daily_update_id = db.Column(db.Integer, db.ForeignKey('daily_job_updates.id'), nullable=True)
    
    company_logo = db.Column(db.String(500), nullable=True)
    
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.Text, nullable=True)
    eligibility = db.Column(db.Text, nullable=True)
    qualification = db.Column(db.String(200), nullable=True)
    experience = db.Column(db.String(100), nullable=True)
    skills = db.Column(db.Text, nullable=True)
    responsibilities = db.Column(db.Text, nullable=True)
    salary = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(150), nullable=True, default='India')
    work_mode = db.Column(db.String(50), nullable=True, default='On-site')
    job_type = db.Column(db.String(50), nullable=True, default='Full-Time')
    
    application_url = db.Column(db.String(500), nullable=False)
    source_url = db.Column(db.String(500), nullable=True)
    application_deadline = db.Column(db.Date, nullable=True, index=True)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    status = db.Column(db.String(20), default='Active', index=True)
    featured = db.Column(db.Boolean, default=False, index=True)
    views = db.Column(db.Integer, default=0)
    
    youtube_video_url = db.Column(db.String(255), nullable=True)
    youtube_video_id = db.Column(db.String(50), nullable=True)
    youtube_title = db.Column(db.String(200), nullable=True)
    youtube_thumbnail = db.Column(db.String(255), nullable=True)
    
    admin_notes = db.Column(db.Text, nullable=True)
    campus_analysis = db.Column(db.Text, nullable=True)
    who_can_apply = db.Column(db.Text, nullable=True)
    resume_tips = db.Column(db.Text, nullable=True)
    interview_tips = db.Column(db.Text, nullable=True)

    seo_title = db.Column(db.String(200), nullable=True)
    seo_description = db.Column(db.String(300), nullable=True)
    seo_keywords = db.Column(db.String(255), nullable=True)
    og_image = db.Column(db.String(255), nullable=True)
    
    duplicate_check_hash = db.Column(db.String(128), nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_logo_url(self):
        if self.company_logo:
            return self.company_logo
        if self.company and self.company.logo:
            return self.company.logo
        return None

    def is_expired(self):
        if self.status == 'Expired':
            return True
        if self.application_deadline and self.application_deadline < datetime.utcnow().date():
            return True
        return False

    def __repr__(self):
        return f'<Job {self.title}>'

class CareerTip(db.Model):
    __tablename__ = 'career_tips'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    category = db.Column(db.String(80), default='Placement Preparation')
    summary = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), default='Campus to Career Team')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CareerTip {self.title}>'

class StudyMaterial(db.Model):
    __tablename__ = 'study_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(50), default='bi-file-earmark-pdf')
    is_premium = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, default=99.0)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudyMaterial {self.title}>'

class PaymentSubmission(db.Model):
    __tablename__ = 'payment_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    txn_id = db.Column(db.String(100), nullable=False, index=True)
    amount = db.Column(db.Float, default=99.0)
    status = db.Column(db.String(20), default='Approved') # Default approved for instant user access
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PaymentSubmission {self.txn_id}>'

class Subscriber(db.Model):
    __tablename__ = 'subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Subscriber {self.email}>'

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ContactMessage {self.subject}>'

class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<SiteSetting {self.key}>'
