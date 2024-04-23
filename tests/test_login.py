from app.models import User, Role
from app.extensions import db
from config import TestConfig
from app import create_app
from flask_security import hash_password


def test_admin_login(client):
    app = create_app(config_class=TestConfig)
    with app.app_context():
        with client:
            new_admin = User(
                username="test_admin",
                password=hash_password("12345678"),
                roles=[Role.query.filter_by(name="administrator").first()],
                active=True,
            )

            db.session.add(new_admin)
            db.session.commit()

            admin = User.query.filter_by(username="test_admin").first()
            test_username = admin.username
            test_password = "12345678"
            response = client.post(
                "/login",
                data=dict(
                    username=test_username,
                    password=test_password,
                ),
            )

        assert response.status_code == 302
        assert response.location == "/admin/"


def test_customer_login(client):
    app = create_app(config_class=TestConfig)
    with app.app_context():
        with client:
            new_customer = User(
                username="test_customer",
                password=hash_password("12345678"),
                roles=[Role.query.filter_by(name="customer").first()],
                active=True,
            )

            db.session.add(new_customer)
            db.session.commit()

            # Query users with roles containing "customer"
            customer = (
                User.query.join(User.roles).filter(Role.name == "customer").first()
            )

            # Loop through each customer and test login
            test_username = customer.username
            test_password = "12345678"
            response = client.post(
                "/customer_login",
                data=dict(username=test_username, password=test_password),
            )

        assert response.status_code == 302
        assert response.location == f"/customer/{test_username}/"
