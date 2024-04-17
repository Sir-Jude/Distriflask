# Actual file containing the tests
from app.models import User


def test_home_title_tab(client):
    response = client.get("/")
    assert "<title>Homepage</title>" in response.data.decode()
    assert "<title>Home</title>" not in response.data.decode()

