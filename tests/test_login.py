from app.models import User, Role
from app import create_app
from sqlalchemy import text


def test_admin_login(client):
    app = create_app()
    with app.app_context():
        test_username = User.query.filter_by(username="admin").first()
        test_password = "12345678"

        # Simulate form submission
        response = client.post(
            "/login", data=dict(username=test_username, password=test_password)
        )

        assert response.status_code == 200
        assert response.location == None


def test_customer_login(client):
    app = create_app()
    with app.app_context():
        # Query users with roles containing "customer"
        customers = User.query.join(User.roles).filter(Role.name == "customer").all()

        # Loop through each customer and test login
        for customer in customers:
            test_username = customer.username
            test_password = "12345678"

        # Simulate form submission
        response = client.post(
            "/customer_login", data=dict(username=test_username, password=test_password)
        )

        assert response.status_code == 200
        assert response.location is None
