import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-fallback-key-for-dev-only'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'campus_to_career.db')
    
    # Handle mysql:// vs mysql+pymysql://
    if SQLALCHEMY_DATABASE_URI.startswith("mysql://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("mysql://", "mysql+pymysql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
