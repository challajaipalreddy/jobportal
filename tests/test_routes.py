def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Campus' in response.data
    assert b'YOUR NEXT OPPORTUNITY' in response.data

def test_jobs_page(client):
    response = client.get('/jobs')
    assert response.status_code == 200
    assert b'Test Engineer' in response.data

def test_job_detail_page(client):
    response = client.get('/jobs/test-engineer')
    assert response.status_code == 200
    assert b'Test Company' in response.data

def test_internships_page(client):
    response = client.get('/internships')
    assert response.status_code == 200

def test_search_jobs(client):
    response = client.get('/jobs?q=Test')
    assert response.status_code == 200
    assert b'Test Engineer' in response.data

def test_filter_jobs_by_category(client):
    response = client.get('/jobs?category=test-category')
    assert response.status_code == 200

def test_contact_page(client):
    response = client.get('/contact')
    assert response.status_code == 200
    assert b'Contact' in response.data
