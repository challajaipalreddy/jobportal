from app.utils import slugify, extract_youtube_id, generate_unique_slug
from app.models import Job, Company

def test_slugify_utility():
    assert slugify("TCS Software Engineer – Freshers") == "tcs-software-engineer-freshers"
    assert slugify("Infosys 2026 Batch Drive!") == "infosys-2026-batch-drive"

def test_youtube_id_extraction():
    url1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    url2 = "https://youtu.be/dQw4w9WgXcQ"
    url3 = "dQw4w9WgXcQ"
    assert extract_youtube_id(url1) == "dQw4w9WgXcQ"
    assert extract_youtube_id(url2) == "dQw4w9WgXcQ"
    assert extract_youtube_id(url3) == "dQw4w9WgXcQ"

def test_unique_slug_generation(app):
    with app.app_context():
        slug1 = generate_unique_slug(Company, "Test Company")
        assert slug1 == "test-company-2"
