from app.models.user import User


def test_password_hashing():
    """Verify that Werkzeug password hashing functions properly."""
    u = User(name="Tester", email="test@test.com")
    u.set_password("SecurePassword999!")
    assert u.check_password("SecurePassword999!")
    assert not u.check_password("WrongPassword")
    assert u.password_hash != "SecurePassword999!"


def test_login_page_renders(client):
    """Test that login page loads with 200 OK."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Welcome Back" in response.data


def test_login_success_and_logout(client, faculty_user):
    """Verify successful authentication and subsequent logout."""
    # Login
    response = client.post('/login', data={
        'email': 'faculty.test@apv.ac.in',
        'password': 'FacultyPass123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back, Test Faculty!" in response.data

    # Logout
    logout_response = client.post('/logout', follow_redirects=True)
    assert logout_response.status_code == 200
    assert b"You have been signed out successfully." in logout_response.data


def test_login_invalid_credentials(client, faculty_user):
    """Verify failed login attempt with wrong password."""
    response = client.post('/login', data={
        'email': 'faculty.test@apv.ac.in',
        'password': 'WrongPassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_deactivated_user_cannot_login(client, app):
    """Ensure inactive users cannot access the system."""
    with app.app_context():
        deactivated = User(
            name="Deactivated Staff",
            email="inactive@apv.ac.in",
            is_active=False
        )
        deactivated.set_password("Password123!")
        from app.extensions import db
        db.session.add(deactivated)
        db.session.commit()

    response = client.post('/login', data={
        'email': 'inactive@apv.ac.in',
        'password': 'Password123!'
    }, follow_redirects=True)
    assert b"Your account is deactivated." in response.data


def test_password_reset_token(app, faculty_user):
    """Test expiring reset token generation and verification."""
    with app.app_context():
        token = faculty_user.get_reset_token()
        verified_user = User.verify_reset_token(token)
        assert verified_user is not None
        assert verified_user.id == faculty_user.id

        # Invalid token verification
        invalid_user = User.verify_reset_token("invalid-tampered-token")
        assert invalid_user is None
