# Actual file containing the tests
from app.models import User


def test_home_title_tab(client):
    response = client.get("/")
    assert b"<title>Homepage</title>" in response.data
    assert b"<title>Home</title>" not in response.data

def test_not_logged_in_customer_home_welcome_message(client):
    response = client.get("/")
    assert b"<h3>Welcome to Your Company!</h3>" in response.data
    assert b"<title>Welcome to Generic Company!</title>" not in response.data