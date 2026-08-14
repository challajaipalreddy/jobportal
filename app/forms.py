from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, BooleanField, DateField
from wtforms.validators import DataRequired, Email, Length, URL, Optional

class LoginForm(FlaskForm):
    email = StringField('Username or Email Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class JobForm(FlaskForm):
    # Basic Information
    title = StringField('Job Title', validators=[DataRequired(), Length(max=200)])
    company_id = SelectField('Select Existing Company', coerce=int, validators=[Optional()])
    new_company_name = StringField('Or Type New Company Name (Auto-creates)', validators=[Optional(), Length(max=100)])
    company_logo = StringField('Company Logo URL (Optional Override)', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    job_type = SelectField('Job Type', choices=[
        ('Full-Time', 'Full-Time'),
        ('Internship', 'Internship'),
        ('Part-Time', 'Part-Time'),
        ('Contract', 'Contract'),
        ('Walk-in Drive', 'Walk-in Drive')
    ], default='Full-Time')
    location = StringField('Location', default='India', validators=[Optional()])
    work_mode = SelectField('Work Mode', choices=[
        ('On-site', 'On-site'),
        ('Remote', 'Remote'),
        ('Hybrid', 'Hybrid')
    ], default='On-site')
    
    # Eligibility & Overview
    qualification = StringField('Educational Qualification', validators=[Optional()])
    experience = StringField('Experience Required', default='0–2 Years', validators=[Optional()])
    skills = TextAreaField('Key Skills (comma separated)', validators=[Optional()])
    eligibility = TextAreaField('Eligibility Criteria', validators=[Optional()])
    
    # Descriptions
    short_description = TextAreaField('Short Summary', validators=[Optional(), Length(max=500)])
    description = TextAreaField('Full Job Description', validators=[DataRequired()])
    responsibilities = TextAreaField('Key Responsibilities', validators=[Optional()])
    salary = StringField('Salary / CTC', validators=[Optional()])
    
    # Application & Sources
    application_url = StringField('Official Application URL', validators=[DataRequired(), URL()])
    source_url = StringField('Source / Official Listing URL', validators=[Optional()])
    application_deadline = DateField('Application Deadline', format='%Y-%m-%d', validators=[Optional()])
    
    # Campus to Career Analysis (Original Value Content)
    campus_analysis = TextAreaField('Campus to Career Analysis (Why consider this job?)', validators=[Optional()])
    who_can_apply = TextAreaField('Who Can Apply?', validators=[Optional()])
    resume_tips = TextAreaField('Resume Preparation Tips', validators=[Optional()])
    interview_tips = TextAreaField('Interview Preparation Guidance', validators=[Optional()])
    admin_notes = TextAreaField('Internal Admin Notes', validators=[Optional()])
    
    # YouTube Video Integration
    has_youtube_video = BooleanField('Attach YouTube Video Explanation for this Job')
    youtube_video_url = StringField('YouTube Video URL', validators=[Optional()])
    youtube_title = StringField('YouTube Video Title', validators=[Optional()])
    
    # SEO Overrides
    seo_title = StringField('SEO Title Tag', validators=[Optional()])
    seo_description = StringField('SEO Meta Description', validators=[Optional()])
    seo_keywords = StringField('SEO Keywords', validators=[Optional()])
    
    # Publishing Controls
    status = SelectField('Status', choices=[
        ('Active', 'Active'),
        ('Draft', 'Draft'),
        ('Expired', 'Expired'),
        ('Closed', 'Closed')
    ], default='Active')
    featured = BooleanField('Mark as Featured Job')
    submit = SubmitField('Save Job Posting')

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    logo = StringField('Company Logo URL or Image Path', validators=[Optional()])
    website = StringField('Official Website URL', validators=[Optional()])
    description = TextAreaField('Company Overview', validators=[Optional()])
    submit = SubmitField('Save Company')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=80)])
    description = TextAreaField('Category Description', validators=[Optional()])
    icon = StringField('Bootstrap Icon Class (e.g. bi-code-slash)', default='bi-briefcase', validators=[Optional()])
    submit = SubmitField('Save Category')

class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Your Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Send Message')

class SubscriberForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Subscribe')

class YouTubeLinkForm(FlaskForm):
    job_id = SelectField('Select Job Posting', coerce=int, validators=[DataRequired()])
    youtube_video_url = StringField('YouTube Video URL', validators=[DataRequired()])
    youtube_title = StringField('Video Title Override (Optional)', validators=[Optional()])
    submit = SubmitField('Attach YouTube Video')
