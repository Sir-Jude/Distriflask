import pytest


@pytest.fixture()
def app():
    app = create_app()
