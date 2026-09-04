import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from extensions import db, bcrypt
from models import User


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        password_hash = bcrypt.generate_password_hash("testpass123").decode("utf-8")
        db.session.add(User(username="testadmin", password_hash=password_hash))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client):
    return client.post("/admin/login", data={"username": "testadmin", "password": "testpass123"}, follow_redirects=True)
