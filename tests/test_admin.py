def test_admin_unauthorized_redirect(client):
    response = client.get('/admin/dashboard')
    assert response.status_code == 302
    assert '/admin/login' in response.location

def test_admin_login_and_dashboard(auth_client):
    response = auth_client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Admin Control Center' in response.data

def test_admin_job_creation(auth_client):
    response = auth_client.post('/admin/jobs/new', data={
        'title': 'New Wipro Role',
        'company_id': 1,
        'category_id': 1,
        'job_type': 'Full-Time',
        'work_mode': 'On-site',
        'location': 'Bangalore',
        'description': 'Comprehensive job description for new role at Wipro.',
        'application_url': 'https://wipro.com/apply',
        'status': 'Active'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Job published successfully!' in response.data
