from app.extensions import db
from app.models import User, Role, Course
from flask_security import hash_password

def test_create_button(admin_login):
    client, _ = admin_login

    response = client.get(
        "/admin/user/new/?url=/admin/user/",
    )

    assert response.status_code == 200
    assert "Save and Add Another" in response.text
