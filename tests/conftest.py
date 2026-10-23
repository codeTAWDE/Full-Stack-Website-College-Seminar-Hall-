import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, Role
from app.models.hall import SeminarHall


@pytest.fixture
def app():
    """Create and configure an isolated test application instance."""
    test_app = create_app('testing')

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def faculty_user(app):
    """Create test faculty user."""
    user = User(
        name="Test Faculty",
        email="faculty.test@apv.ac.in",
        role=Role.FACULTY,
        department="Computer Engineering",
        is_active=True
    )
    user.set_password("FacultyPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def principal_user(app):
    """Create test principal user."""
    user = User(
        name="Test Principal",
        email="principal.test@apv.ac.in",
        role=Role.PRINCIPAL,
        department="Administration",
        is_active=True
    )
    user.set_password("PrincipalPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app):
    """Create test administrator user."""
    user = User(
        name="Test Admin",
        email="admin.test@apv.ac.in",
        role=Role.ADMIN,
        department="IT",
        is_active=True
    )
    user.set_password("AdminPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_hall(app):
    """Create test seminar hall."""
    hall = SeminarHall(
        name="Main Auditorium",
        code="AUD-TEST",
        location="Campus Block A",
        capacity=200,
        description="Test Auditorium",
        is_active=True
    )
    db.session.add(hall)
    db.session.commit()
    return hall