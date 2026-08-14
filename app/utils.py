import re
import unicodedata
from flask import current_app

def slugify(text):
    """
    Converts string to lowercase slug, removing non-alphanumeric chars.
    Example: 'TCS Software Engineer – Freshers' -> 'tcs-software-engineer-freshers'
    """
    if not text:
        return ''
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def extract_youtube_id(url):
    """
    Extracts 11-character YouTube video ID from various URL formats.
    Supports:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ
    - https://www.youtube.com/embed/dQw4w9WgXcQ
    - https://www.youtube.com/shorts/dQw4w9WgXcQ
    - dQw4w9WgXcQ (raw ID)
    """
    if not url:
        return None
    url = url.strip()
    if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
        
    pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?|shorts)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def generate_unique_slug(model_class, title_text, current_id=None):
    """
    Generates a unique slug for a given model.
    Appends -2, -3 if duplicate found.
    """
    base_slug = slugify(title_text)
    if not base_slug:
        base_slug = 'item'
        
    slug = base_slug
    counter = 1
    
    query = model_class.query.filter_by(slug=slug)
    if current_id:
        query = query.filter(model_class.id != current_id)
        
    while query.first() is not None:
        counter += 1
        slug = f"{base_slug}-{counter}"
        query = model_class.query.filter_by(slug=slug)
        if current_id:
            query = query.filter(model_class.id != current_id)
            
    return slug

def allowed_file(filename):
    """
    Validates uploaded file extensions.
    """
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']
