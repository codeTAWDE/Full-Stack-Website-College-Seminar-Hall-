def test_public_pages(client):
    """Verify public endpoints return 200 OK."""
    assert client.get('/').status_code == 200
    assert client.get('/health').status_code == 200
    assert client.get('/calendar').status_code == 200
    assert client.get('/halls').status_code == 200


def test_faculty_role_access(client, faculty_user, sample_hall):
    """Verify faculty access boundaries."""
    # Authenticate faculty
    client.post('/login', data={
        'email': 'faculty.test@apv.ac.in',
        'password': 'FacultyPass123!'
    })

    # Faculty can access their own portal
    assert client.get('/faculty/dashboard').status_code == 200
    assert client.get('/faculty/bookings/new').status_code == 200

    # Faculty is FORBIDDEN from Principal portal (403)
    assert client.get('/principal/dashboard').status_code == 403
    assert client.get('/principal/pending').status_code == 403

    # Faculty is FORBIDDEN from Admin Console (403)
    assert client.get('/admin/dashboard').status_code == 403
    assert client.get('/admin/users').status_code == 403
    assert client.get('/admin/halls').status_code == 403


def test_principal_role_access(client, principal_user):
    """Verify principal can access approval endpoints."""
    client.post('/login', data={
        'email': 'principal.test@apv.ac.in',
        'password': 'PrincipalPass123!'
    })

    # Principal can access dashboard and pending approvals
    assert client.get('/principal/dashboard').status_code == 200
    assert client.get('/principal/pending').status_code == 200

    # Principal cannot access System Admin user controls
    assert client.get('/admin/users').status_code == 403


def test_admin_role_access(client, admin_user):
    """Verify administrator has full system access."""
    client.post('/login', data={
        'email': 'admin.test@apv.ac.in',
        'password': 'AdminPass123!'
    })

    assert client.get('/admin/dashboard').status_code == 200
    assert client.get('/admin/halls').status_code == 200
    assert client.get('/admin/users').status_code == 200
    assert client.get('/admin/audit-logs').status_code == 200
    assert client.get('/admin/reports').status_code == 200


def test_calendar_api_endpoint(client):
    """Verify calendar events API returns valid JSON format."""
    response = client.get('/api/calendar/events')
    assert response.status_code == 200
    assert response.is_json
    assert isinstance(response.get_json(), list)
